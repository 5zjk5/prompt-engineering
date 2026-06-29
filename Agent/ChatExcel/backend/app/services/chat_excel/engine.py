"""模块1 — ChatExcel 引擎

支持同一会话多文件、多 sheet：
- 上传后每个非空 sheet 落一张 DuckDB 表
- 学习阶段并行学习所有待学习表
- 问答阶段基于全量表结构进行跨表关联分析
"""

import asyncio
import json
import logging
import re
import uuid
from datetime import date, datetime
from typing import AsyncIterator, Dict, List, Optional

from app.services.chat_excel.reader import ExcelReader
from app.llm.client import chat_completion_stream, chat_completion_full
from app.dal.conversation import add_message, get_messages
from app.prompts.chat_excel_analyze import (
    build_analyze_messages,
    build_table_selection_messages,
    parse_table_selection,
)
from app.prompts.chat_excel_learning import (
    build_learning_messages,
    parse_learning_response,
    build_learning_view_message,
)
from app.core.logger import get_session_logger
from app.llm.llm_config import get_default_llm_provider
from app.core import config

logger = logging.getLogger(__name__)


def _json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, (bytes, bytearray)):
        return obj.decode("utf-8", errors="replace")
    raise TypeError(f"Type {type(obj)} not serializable")


def _normalize_chart_type(chart_type: str) -> str:
    chart_type = (chart_type or "").strip()
    if not chart_type or chart_type.lower() in ("table", "response table"):
        return "response_table"
    return chart_type


def parse_api_call(text: str) -> Optional[Dict]:
    """从 LLM 输出中解析 <api-call> 格式"""
    pattern = r"<api-call>\s*<name>\s*(.*?)\s*</name>\s*<args>\s*<sql>\s*(.*?)\s*</sql>\s*</args>\s*</api-call>"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return {
            "chart_type": _normalize_chart_type(match.group(1)),
            "sql": match.group(2).strip(),
        }
    return None


def _api_call_started(text: str) -> bool:
    return "<api-call>" in text


def _api_call_ready(text: str) -> bool:
    return text.count("<api-call>") > 0 and text.count("<api-call>") == text.count("</api-call>")


def _text_before_api_call(text: str) -> str:
    """提取 <api-call> 之前的可见文本，同时避免部分标签泄漏到前端。"""
    idx = text.find("<api-call>")
    if idx >= 0:
        return text[:idx]
    tag = "<api-call>"
    for i in range(len(tag), 0, -1):
        if text.endswith(tag[:i]):
            return text[:-i]
    return text


def _remove_api_call(text: str) -> str:
    return re.sub(r"<api-call>[\s\S]*?</api-call>", "", text).strip()


def _chart_view_content(chart_type: str, sql: str, data: list) -> str:
    return json.dumps(
        {
            "type": chart_type or "response_table",
            "sql": sql,
            "data": data,
        },
        ensure_ascii=False,
        default=_json_serial,
    )


class ChatExcelEngine:
    """模块1 ChatExcel 引擎 — 一个会话对应多个 Excel 表。"""

    def __init__(self, conv_uid: str, file_path: str = "", file_name: str = ""):
        self.conv_uid = conv_uid or uuid.uuid4().hex
        self.logger = get_session_logger(self.conv_uid, "chat_excel")
        self.reader = ExcelReader.get_or_create(self.conv_uid)
        self.file_name = file_name
        self._learned = self.reader._transformed
        self._last_added_tables: List[dict] = []
        if file_path:
            self._last_added_tables = self.reader.add_file(file_path, file_name)
            if self._last_added_tables:
                self._learned = False
                self.logger.info("初始化时加载文件: %s, 新增 %d 个表", file_path, len(self._last_added_tables))
        self.logger.info("ChatExcelEngine 初始化完成: conv_uid=%s, table_infos=%d", self.conv_uid, len(self.reader.table_infos))

    def add_file(self, file_path: str, file_name: str = "") -> List[dict]:
        self.logger.info("add_file: file_path=%s, file_name=%s", file_path, file_name)
        added = self.reader.add_file(file_path, file_name)
        self._last_added_tables = added
        if added:
            self._learned = False
            self.logger.info("新增 %d 个表: %s", len(added), [a.get("temp_table") for a in added])
        else:
            self.logger.info("文件已存在，无新增表")
        return added

    async def _learn_table(self, table_info: dict, progress: dict = None) -> dict:
        """学习单张表。progress 为共享计数器，用于打印学习进度。"""
        if progress is not None:
            progress["done"] += 1
            self.logger.info("当前学习 %d/%d: sheet_name=%s",
                             progress["done"], progress["total"], table_info.get("sheet_name"))
        else:
            self.logger.info("开始学习表: temp_table=%s, file_name=%s, sheet_name=%s",
                             table_info["temp_table"], table_info.get("file_name"), table_info.get("sheet_name"))
        table_schema = self.reader.get_create_table_sql(table_name=table_info["temp_table"])
        columns, datas = self.reader.get_sample_data(table_name=table_info["temp_table"])
        data_example = json.dumps(
            {"columns": columns, "rows": datas},
            ensure_ascii=False,
            default=_json_serial,
        )
        table_summary = self.reader.get_summary(table_name=table_info["temp_table"])
        messages = build_learning_messages(
            table_schema=table_schema,
            data_example=data_example,
            table_summary=table_summary,
            file_name=table_info.get("file_name") or self.file_name,
        )
        self.logger.info("学习提示词已构建，共 %d 条消息", len(messages))
        self.logger.info(
            "===== [LEARN_PROMPT_FULL] 学习阶段完整输入 messages =====\n%s\n===== [LEARN_PROMPT_FULL_END] =====",
            json.dumps(messages, ensure_ascii=False, indent=2, default=_json_serial),
        )

        default_llm = get_default_llm_provider()
        # 学习阶段需要输出完整的列分析 JSON，列数多的宽表输出量很大，
        # 使用更大的 max_tokens 避免输出截断导致 JSON 解析失败回退
        _LEARN_MAX_TOKENS = 16384
        self.logger.info(
            "LLM 调用参数: stage=learn, model=%s, temperature=%s, max_tokens=%s, stream=%s, messages=%d",
            default_llm.model,
            0.8,
            _LEARN_MAX_TOKENS,
            False,
            len(messages),
        )
        llm_result = await chat_completion_full(
            messages,
            temperature=0.8,
            max_tokens=_LEARN_MAX_TOKENS,
            logger=self.logger,
            preferred_model=getattr(self, '_model_name', '') or None,
        )
        self.logger.info("LLM 学习完成，返回长度=%d", len(llm_result))
        self.logger.info(
            "===== [LEARN_LLM_OUTPUT_FULL] 学习阶段完整模型输出 =====\n%s\n===== [LEARN_LLM_OUTPUT_FULL_END] =====",
            llm_result,
        )

        parsed = parse_learning_response(llm_result)
        if parsed.get("column_analysis"):
            self.reader.transform_table(parsed, table_info=table_info)
            self.logger.info("表转换完成，column_analysis 数量=%d", len(parsed.get("column_analysis", [])))
        else:
            logger.warning("LLM returned no column_analysis, falling back to direct copy")
            self.reader._fallback_copy_table(table_info)
            self.logger.warning("回退到直接复制表: %s", table_info["temp_table"])

        parsed["file_name"] = table_info.get("file_name", "")
        parsed["sheet_name"] = table_info.get("sheet_name", "")
        parsed["table_name"] = table_info.get("table_name", "")
        parsed["view_message"] = build_learning_view_message(parsed)
        self.logger.info("表学习完成: table_name=%s", parsed.get("table_name"))
        return parsed

    async def learn(self) -> dict:
        """学习本次新增的表；没有新增表时才兜底学习未学习表。"""
        self.logger.info("===== [LEARN] 开始数据学习 =====")
        pending_tables = [table for table in self._last_added_tables if not table.get("transformed")]
        if not pending_tables:
            pending_tables = list(self.reader.pending_table_infos)
        if not pending_tables:
            self.logger.info("没有待学习的表")
            self._learned = self.reader._transformed
            self._last_added_tables = []
            return {}
        self.logger.info("待学习表数量: %d", len(pending_tables))

        # 限制并发数，避免表过多时同时发起大量 LLM 调用导致限流或超时
        _LEARN_CONCURRENCY = 5
        semaphore = asyncio.Semaphore(_LEARN_CONCURRENCY)
        progress = {"done": 0, "total": len(pending_tables)}

        async def _learn_with_limit(table_info):
            async with semaphore:
                return await self._learn_table(table_info, progress=progress)

        results = await asyncio.gather(
            *(_learn_with_limit(table_info) for table_info in pending_tables),
            return_exceptions=True,
        )

        learned_tables = []
        for table_info, result in zip(pending_tables, results):
            if isinstance(result, Exception):
                self.logger.error("学习表失败: %s, 错误: %s", table_info.get("temp_table"), result)
                self.reader._fallback_copy_table(table_info)
                fallback = {
                    "file_name": table_info.get("file_name", ""),
                    "sheet_name": table_info.get("sheet_name", ""),
                    "table_name": table_info.get("table_name", ""),
                    "data_analysis": "该表学习失败，已按原始字段保留用于后续分析。",
                    "column_analysis": [],
                    "analysis_program": [],
                }
                fallback["view_message"] = build_learning_view_message(fallback)
                learned_tables.append(fallback)
            else:
                learned_tables.append(result)

        self._learned = self.reader._transformed
        self._last_added_tables = []
        view_message = "\n\n".join(item.get("view_message", "") for item in learned_tables if item.get("view_message"))
        self.logger.info("===== [LEARN] 数据学习完成，成功 %d 个表 =====", len(learned_tables))
        return {"tables": learned_tables, "view_message": view_message}

    async def _load_chat_history(self) -> List[dict]:
        """加载最近 10 轮历史消息，跳过学习阶段的 view_message（避免重复注入已学习表的信息）。"""
        try:
            db_messages = await get_messages(self.conv_uid)
            history = []
            for msg in db_messages:
                if msg.get("role") == "human":
                    history.append({"role": "user", "content": msg["content"]})
                elif msg.get("role") == "ai":
                    content = msg.get("content", "")
                    if msg.get("metadata"):
                        try:
                            meta = json.loads(msg["metadata"])
                            if meta.get("content"):
                                content = meta["content"]
                        except (json.JSONDecodeError, TypeError):
                            pass
                    # 跳过学习阶段的 view_message（以 "### **表：" 开头），
                    # 这些信息已通过 DDL 的列 COMMENT 注入 system prompt，不需要重复作为历史
                    if content.lstrip().startswith("### **表："):
                        continue
                    # 去掉 <chart-view> 标签，防止 LLM 模仿该格式而跳过 <api-call> SQL 执行
                    content = re.sub(r"<chart-view\s+content='.*?'\s*/>", "", content, flags=re.DOTALL)
                    history.append({"role": "assistant", "content": content})
            limited_history = history[-config.CHAT_EXCEL_HISTORY_ROUNDS * 2 :]
            self.logger.info("加载历史消息: 数据库 %d 条, 处理后 %d 条, 本次使用 %d 条", len(db_messages), len(history), len(limited_history))
            self.logger.info(
                "===== [CHAT_HISTORY_FULL] 本次分析使用的完整历史消息 =====\n%s\n===== [CHAT_HISTORY_FULL_END] =====",
                json.dumps(limited_history, ensure_ascii=False, indent=2, default=_json_serial),
            )
            return limited_history
        except Exception as e:
            self.logger.warning("加载历史消息失败: %s", e)
            return []

    async def _next_order_no(self) -> int:
        try:
            return len(await get_messages(self.conv_uid))
        except Exception:
            return 0

    async def _save_ai_message(self, content: str, metadata: dict | None = None) -> None:
        """保存 AI 消息，供前端从数据库恢复历史展示。"""
        if not content and not metadata:
            return
        order_no = await self._next_order_no()
        self.logger.info("保存 AI 消息: order_no=%d", order_no)
        await add_message(
            self.conv_uid,
            "ai",
            content,
            order_no=order_no,
            metadata=json.dumps(metadata or {}, ensure_ascii=False),
        )

    async def _save_round(self, user_input: str, content: str, metadata: dict | None = None) -> None:
        """保存一轮用户提问和 AI 回复，供前端从数据库恢复历史展示。"""
        order_no = await self._next_order_no()
        self.logger.info("保存对话轮次: order_no=%d", order_no)
        if user_input:
            await add_message(self.conv_uid, "human", user_input, order_no=order_no)
            order_no += 1
        await add_message(
            self.conv_uid,
            "ai",
            content,
            order_no=order_no,
            metadata=json.dumps(metadata or {}, ensure_ascii=False),
        )

    async def chat_stream(self, user_input: str, model_name: str = "") -> AsyncIterator[dict]:
        """流式对话。model_name 指定用户首选模型，优先使用。"""
        self._model_name = model_name
        full_text = ""
        view_message = ""
        saved_learning_content = ""
        saved_sql = ""
        saved_chart_type = ""
        saved_chart_data = None
        try:
            if self._last_added_tables or self.reader.pending_table_infos:
                self.logger.info("【学习阶段】有待学习表，开始学习")
                yield {"type": "learning", "content": "正在分析数据结构..."}
                learning_result = await self.learn()
                if learning_result.get("view_message"):
                    saved_learning_content = learning_result["view_message"]
                    self.logger.info("学习结果 view_message 长度=%d", len(learning_result["view_message"]))
                    yield {
                        "type": "learning_result",
                        "content": learning_result["view_message"],
                    }
                yield {"type": "learning_done"}
                self.logger.info("学习阶段完成")

            if not user_input or not user_input.strip():
                self.logger.info("用户输入为空，直接结束")
                if saved_learning_content:
                    await self._save_ai_message(
                        saved_learning_content,
                        {
                            "content": saved_learning_content,
                            "chartData": None,
                        },
                    )
                yield {"type": "done"}
                return

            self.logger.info("===== [ANALYZE] 开始分析 =====")
            self.logger.info("用户输入: %s", user_input[:200])

            chat_history = await self._load_chat_history()
            table_names = self.reader.table_names
            self.logger.info("可用表: %s", table_names)
            if not table_names:
                self.logger.warning("没有可分析的数据表")
                yield {"type": "error", "content": "当前会话没有可分析的数据表，请先上传并完成 Excel 学习。"}
                yield {"type": "done"}
                return

            # ---- 表筛选：用轻量 LLM 调用判断用户问题涉及哪些表，只把相关表的 DDL + 采样注入 prompt ----
            selected_tables = table_names  # 默认全部表
            try:
                table_index = self.reader.get_table_index()
                if len(table_index) > 1:
                    selection_messages = build_table_selection_messages(user_input, table_index)
                    self.logger.info("===== [TABLE_SELECTION_PROMPT] 表筛选提示词 =====\n%s\n===== [TABLE_SELECTION_PROMPT_END] =====",
                                     json.dumps(selection_messages, ensure_ascii=False, indent=2, default=_json_serial))
                    selection_response = await chat_completion_full(
                        selection_messages,
                        temperature=0.0,
                        logger=self.logger,
                        preferred_model=model_name or None,
                    )
                    self.logger.info("表筛选 LLM 返回: %s", selection_response)
                    selected_tables = parse_table_selection(selection_response, table_names)
                    self.logger.info("表筛选结果: %s (共 %d/%d 张表)", selected_tables, len(selected_tables), len(table_names))
                else:
                    self.logger.info("仅 1 张表，跳过表筛选")
            except Exception as e:
                self.logger.warning("表筛选失败，使用全部表: %s", e)
                selected_tables = table_names

            # 只拼接选中表的 DDL（含列注释）和采样数据（2行）
            table_schema = self.reader.get_create_table_sql_for_tables(selected_tables)
            data_example = self.reader.get_sample_data_for_tables(selected_tables, limit=2)
            self.logger.info("选中表 DDL 长度=%d, 采样数据长度=%d", len(table_schema), len(data_example))

            messages = build_analyze_messages(
                user_input=user_input,
                table_schema=table_schema,
                data_example=data_example,
                table_name=", ".join(table_names),
                table_names=table_names,
                chat_history=chat_history,
            )
            self.logger.info("分析提示词已构建，共 %d 条消息", len(messages))
            self.logger.info(
                "===== [ANALYZE_PROMPT_FULL] 分析阶段完整输入 messages =====\n%s\n===== [ANALYZE_PROMPT_FULL_END] =====",
                json.dumps(messages, ensure_ascii=False, indent=2, default=_json_serial),
            )

            previous_visible = ""
            sql_executed = False
            default_llm = get_default_llm_provider()
            self.logger.info(
                "LLM 调用参数: stage=analyze, model=%s, temperature=%s, max_tokens=%s, stream=%s, messages=%d",
                default_llm.model,
                default_llm.temperature,
                default_llm.max_tokens,
                True,
                len(messages),
            )
            self.logger.info("开始 LLM 流式调用")
            # 通过回调捕获后端实际使用的模型，切换时通知前端
            current_provider = {"name": None}
            def _on_provider(name):
                current_provider["name"] = name
            async for chunk in chat_completion_stream(messages, logger=self.logger, preferred_model=model_name or None, on_provider=_on_provider):
                if current_provider["name"]:
                    yield {"type": "model", "model": current_provider["name"]}
                    current_provider["name"] = None
                full_text += chunk

                visible_text = _text_before_api_call(full_text)
                if visible_text and len(visible_text) > len(previous_visible):
                    delta = visible_text[len(previous_visible) :]
                    previous_visible = visible_text
                    view_message += delta
                    yield {"type": "text", "content": delta}

                if _api_call_started(full_text) and _api_call_ready(full_text) and not sql_executed:
                    api_call = parse_api_call(full_text)
                    if not api_call:
                        self.logger.warning("<api-call> 标签闭合但解析失败")
                        sql_executed = True
                        continue
                    sql_executed = True
                    self.logger.info("解析到 SQL: chart_type=%s", api_call["chart_type"])
                    self.logger.info(
                        "===== [ANALYZE_SQL_FULL] 模型生成的完整 SQL =====\n%s\n===== [ANALYZE_SQL_FULL_END] =====",
                        api_call["sql"],
                    )

                    saved_sql = api_call["sql"]
                    saved_chart_type = api_call["chart_type"]
                    yield {"type": "sql", "content": api_call["sql"]}
                    try:
                        df = self.reader.get_df_by_sql(api_call["sql"])
                        split_data = json.loads(
                            df.to_json(
                                orient="split",
                                date_format="iso",
                                date_unit="s",
                                force_ascii=False,
                            )
                        )
                        chart_data = {"columns": split_data["columns"], "rows": split_data["data"]}
                        saved_chart_data = chart_data
                        chart_view = _chart_view_content(api_call["chart_type"], api_call["sql"], chart_data)
                        view_message += f"<chart-view content='{chart_view}'/>"
                        self.logger.info("SQL 执行成功，返回 %d 行", len(split_data.get("data", [])))
                        yield {
                            "type": "chart",
                            "chart_type": api_call["chart_type"],
                            "sql": api_call["sql"],
                            "data": chart_data,
                            "chart_view": chart_view,
                        }
                    except Exception as e:
                        self.logger.error("SQL 执行失败: %s", e)
                        err_msg = f"SQL 执行失败: {str(e)}"
                        view_message += err_msg
                        yield {"type": "text", "content": err_msg}

            if _api_call_started(full_text) and not sql_executed:
                self.logger.warning("LLM 输出包含不完整的 <api-call> 标签，尝试兜底")
                loose_match = re.search(r"<sql>\s*(.*?)\s*</sql>", full_text, re.DOTALL)
                if loose_match:
                    fallback_sql = loose_match.group(1).strip()
                    self.logger.info(
                        "===== [ANALYZE_FALLBACK_SQL_FULL] 兜底匹配的完整 SQL =====\n%s\n===== [ANALYZE_FALLBACK_SQL_FULL_END] =====",
                        fallback_sql,
                    )
                    saved_sql = fallback_sql
                    yield {"type": "sql", "content": fallback_sql}
                    try:
                        df = self.reader.get_df_by_sql(fallback_sql)
                        split_data = json.loads(df.to_json(orient="split", date_format="iso", date_unit="s", force_ascii=False))
                        chart_data = {"columns": split_data["columns"], "rows": split_data["data"]}
                        name_match = re.search(r"<name>\s*(.*?)\s*</name>", full_text)
                        chart_type = name_match.group(1).strip() if name_match else "response_table"
                        saved_chart_type = chart_type
                        saved_chart_data = chart_data
                        chart_view = _chart_view_content(chart_type, fallback_sql, chart_data)
                        view_message += f"<chart-view content='{chart_view}'/>"
                        self.logger.info("兜底 SQL 执行成功")
                        yield {"type": "chart", "chart_type": chart_type, "sql": fallback_sql, "data": chart_data, "chart_view": chart_view}
                    except Exception as e:
                        self.logger.error("兜底 SQL 执行失败: %s", e)
                        yield {"type": "text", "content": f"\nSQL 执行失败: {str(e)}"}
                else:
                    self.logger.warning("兜底匹配失败，无有效 SQL")
                    yield {"type": "text", "content": "\n模型未能生成完整的数据查询，请重新提问或换个问法。"}
            elif not _api_call_started(full_text) and full_text:
                remainder = full_text[len(previous_visible):]
                if remainder:
                    view_message += remainder
                    yield {"type": "text", "content": remainder}

            self.logger.info("===== [ANALYZE] 分析完成，full_text长度=%d =====", len(full_text))
            self.logger.info(
                "===== [ANALYZE_LLM_OUTPUT_FULL] 分析阶段流式完整模型输出 =====\n%s\n===== [ANALYZE_LLM_OUTPUT_FULL_END] =====",
                full_text,
            )
            await self._save_round(
                user_input,
                view_message,
                {
                    "content": view_message,
                    "sql": saved_sql,
                    "chartType": saved_chart_type,
                    "chartData": saved_chart_data,
                },
            )
            yield {"type": "done"}
        except Exception as e:
            logger.error(f"chat_stream error: {e}", exc_info=True)
            self.logger.error("chat_stream 异常: %s", e)
            yield {"type": "error", "content": str(e)}
            yield {"type": "done"}
