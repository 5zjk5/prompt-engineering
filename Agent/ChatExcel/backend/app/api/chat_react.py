"""模块3 ReAct Agent API 接口 — SSE 流式

1:1 复刻原版 agentic_data_api.py 的 /react-agent 接口

支持两种场景:
1. 有文件: 完整 ReAct Agent 循环（execute_analysis → code_interpreter → html_interpreter → terminate）
2. 无文件: 纯 LLM 对话（用于基础连通测试）
"""

import json
import time
import traceback
import uuid

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.react_agent.engine import ReactEngine
from app.llm.client import chat_completion_stream
from app.dal.conversation import add_message, create_conversation, get_conversation, get_messages
from app.core.logger import get_session_logger
from app.llm.llm_config import get_default_llm_provider
from app.core import config

router = APIRouter()

# 会话级引擎缓存 — conv_uid → ReactEngine
_engines: dict = {}


def _next_order_no(messages: list[dict]) -> int:
    """根据已有消息数量计算下一条消息顺序号。"""
    return len(messages)


def _find_step(steps: list[dict], step_id: str) -> dict | None:
    """按步骤 ID 查找 ReAct 步骤。"""
    for step in steps:
        if step.get("id") == step_id:
            return step
    return None


def _apply_react_event(steps: list[dict], event: dict) -> None:
    """把 ReAct 流式事件转换成前端历史恢复需要的步骤结构。"""
    event_type = event.get("type")
    step_id = event.get("id", "")
    if event_type == "step.start":
        steps.append(
            {
                "id": step_id or f"step_{len(steps) + 1}",
                "step": event.get("step", len(steps) + 1),
                "title": event.get("title", ""),
                "thought": "",
                "action": "",
                "actionInput": None,
                "output": [],
                "status": "running",
            }
        )
    elif event_type == "step.meta":
        step = _find_step(steps, step_id)
        if step:
            step["thought"] = event.get("thought") or step.get("thought", "")
            step["action"] = event.get("action") or step.get("action", "")
            step["actionInput"] = event.get("action_input", step.get("actionInput"))
    elif event_type == "step.chunk":
        step = _find_step(steps, step_id)
        if step:
            output_type = event.get("output_type") or "text"
            if output_type == "thought":
                step["thought"] = event.get("content") or step.get("thought", "")
            elif output_type == "text":
                last_idx = len(step["output"]) - 1
                last = step["output"][last_idx] if last_idx >= 0 else ""
                if last.startswith('{"output_type":"text"'):
                    try:
                        parsed = json.loads(last)
                        parsed["content"] = f"{parsed.get('content', '')}{event.get('content', '')}"
                        step["output"][last_idx] = json.dumps(parsed, ensure_ascii=False)
                    except Exception:
                        step["output"].append(json.dumps({"output_type": "text", "content": event.get("content", "")}, ensure_ascii=False))
                else:
                    step["output"].append(json.dumps({"output_type": "text", "content": event.get("content", "")}, ensure_ascii=False))
            else:
                step["output"].append(json.dumps({"output_type": output_type, "content": event.get("content"), "title": event.get("title")}, ensure_ascii=False))
    elif event_type == "step.done":
        step = _find_step(steps, step_id)
        if step:
            step["status"] = "completed" if event.get("status") == "done" else "error"
            if event.get("status") == "failed":
                step["error"] = "Step failed"


async def _save_react_round(conv_uid: str, user_input: str, content: str, steps: list[dict], elapsed_ms: int, logger) -> None:
    """保存 ReAct 一轮用户提问和 AI 回复，供前端从数据库恢复历史展示。"""
    if not user_input and not content and not steps:
        return
    order_no = _next_order_no(await get_messages(conv_uid))
    if user_input:
        await add_message(conv_uid, "human", user_input, order_no=order_no)
        order_no += 1
    metadata = json.dumps(
        {
            "steps": steps,
            "finalContent": content,
            "elapsedMs": elapsed_ms,
            "content": "",
        },
        ensure_ascii=False,
    )
    await add_message(conv_uid, "ai", "", order_no=order_no, metadata=metadata)
    logger.info("ReAct 对话已保存: order_no=%d, steps=%d, final_len=%d", order_no, len(steps), len(content or ""))


async def _load_react_history(conv_uid: str, logger) -> list[dict]:
    """加载最近 10 轮 ReAct 历史消息，拼接为 LLM messages 格式。"""
    try:
        db_messages = await get_messages(conv_uid)
        history = []
        for msg in db_messages:
            if msg.get("role") == "human":
                history.append({"role": "user", "content": msg["content"]})
            elif msg.get("role") == "ai":
                content = msg.get("content", "")
                # ReAct 的回复内容存在 metadata.finalContent 字段
                if msg.get("metadata"):
                    try:
                        meta = json.loads(msg["metadata"])
                        content = meta.get("finalContent") or meta.get("content") or content
                    except (json.JSONDecodeError, TypeError):
                        pass
                if content:
                    history.append({"role": "assistant", "content": content})
        # 最近 N 轮（每轮 human + ai = 2 条），N 由配置项 REACT_HISTORY_ROUNDS 控制
        limited_history = history[-config.REACT_HISTORY_ROUNDS * 2:]
        logger.info("加载历史消息: 数据库 %d 条, 处理后 %d 条, 本次使用 %d 条", len(db_messages), len(history), len(limited_history))
        return limited_history
    except Exception as e:
        logger.warning("加载历史消息失败: %s", e)
        return []


class ChatReactRequest(BaseModel):
    user_input: str
    conv_uid: str = ""
    file_path: str = ""
    file_name: str = ""
    file_paths: list[str] = []
    file_names: list[str] = []
    model_name: str = ""
    skill_name: str = ""


@router.post("/react-agent")
async def chat_react_agent(req: ChatReactRequest):
    """模块3 ReAct Agent — SSE 流式接口

    1:1 复刻原版逻辑:
    - 无文件 + 无已有引擎 → 纯 LLM 对话
    - 有文件 → 创建/复用 ReactEngine → ReAct 循环
    - 已有引擎 → 复用引擎（即使本次请求没传 file_path）
    """
    conv_uid = req.conv_uid or uuid.uuid4().hex
    logger = get_session_logger(conv_uid, "react_agent")
    logger.info("===== [REACT_AGENT] 收到对话请求 =====")
    logger.info("参数: user_input=%s, conv_uid=%s, file_path=%s, skill_name=%s, file_paths=%s",
                req.user_input[:100] if req.user_input else "", conv_uid, req.file_path, req.skill_name, req.file_paths)

    # 判断是否需要走 ReAct 引擎
    has_engine = conv_uid in _engines
    # 优先使用 file_paths（多文件），否则回退到 file_path（单文件）
    file_paths = req.file_paths if req.file_paths else ([req.file_path] if req.file_path else [])
    file_names = req.file_names if req.file_names else ([req.file_name] if req.file_name else [])
    has_file = bool(file_paths)

    # 无文件 + 无已有引擎时，尝试从数据库恢复文件信息（容器重启后引擎缓存丢失的场景）
    if not has_file and not has_engine and conv_uid:
        try:
            conv = await get_conversation(conv_uid)
            if conv:
                saved_paths = conv.get("file_paths") or []
                saved_names = conv.get("file_names") or []
                if saved_paths:
                    file_paths = saved_paths
                    file_names = saved_names if saved_names else ["" for _ in saved_paths]
                    has_file = True
                    logger.info("从数据库恢复文件信息: file_paths=%s", file_paths)
        except Exception as e:
            logger.warning("从数据库恢复文件信息失败: %s", e)

    # 无文件 + 无已有引擎 → 纯 LLM 对话
    if not has_file and not has_engine:
        logger.info("【分支1】无文件+无引擎，走纯 LLM 对话")
        async def simple_chat_stream():
            try:
                start_time = time.perf_counter()
                steps = []
                step_id = "step_1"
                start_event = {'type': 'step.start', 'step': 1, 'id': step_id, 'title': '分析中'}
                meta_event = {'type': 'step.meta', 'id': step_id, 'thought': req.user_input, 'action': '', 'action_input': {}}
                _apply_react_event(steps, start_event)
                _apply_react_event(steps, meta_event)
                yield f"data: {json.dumps(start_event, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps(meta_event, ensure_ascii=False)}\n\n"

                full_text = ""
                # 加载历史对话并拼接当前输入
                chat_history = await _load_react_history(conv_uid, logger)
                messages = chat_history + [{"role": "user", "content": req.user_input}]
                default_llm = get_default_llm_provider()
                logger.info("纯 LLM 对话调用，user_input=%s", req.user_input[:100])
                logger.info(
                    "LLM 调用参数: stage=react_simple, model=%s, temperature=%s, max_tokens=%s, stream=%s, messages=%d",
                    default_llm.model,
                    0.7,
                    default_llm.max_tokens,
                    True,
                    len(messages),
                )
                logger.info(
                    "===== [REACT_INPUT_FULL] 本次对话输入完整消息 =====\n%s\n===== [REACT_INPUT_FULL_END] =====",
                    json.dumps(messages, ensure_ascii=False, indent=2),
                )
                # 通过回调捕获后端实际使用的模型，切换时通知前端
                current_provider = {"name": None}
                def _on_provider(name):
                    current_provider["name"] = name
                async for chunk in chat_completion_stream(
                    messages=messages,
                    temperature=0.7,
                    logger=logger,
                    preferred_model=req.model_name or None,
                    on_provider=_on_provider,
                ):
                    if current_provider["name"]:
                        model_event = {'type': 'model', 'model': current_provider["name"]}
                        yield f"data: {json.dumps(model_event, ensure_ascii=False)}\n\n"
                        current_provider["name"] = None
                    full_text += chunk
                    chunk_event = {'type': 'step.chunk', 'id': step_id, 'output_type': 'text', 'content': chunk}
                    _apply_react_event(steps, chunk_event)
                    yield f"data: {json.dumps(chunk_event, ensure_ascii=False)}\n\n"

                logger.info(
                    "===== [REACT_OUTPUT_FULL] 本次对话输出完整内容 =====\n%s\n===== [REACT_OUTPUT_FULL_END] =====",
                    full_text,
                )

                done_event = {'type': 'step.done', 'id': step_id, 'status': 'done'}
                _apply_react_event(steps, done_event)
                final_content = full_text or '(无回复)'
                yield f"data: {json.dumps(done_event, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'final', 'content': final_content}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                await _save_react_round(conv_uid, req.user_input, final_content, steps, elapsed_ms, logger)
                logger.info("纯 LLM 对话完成，共计 %d 字符", len(full_text))
            except Exception as exc:
                logger.error("ReAct SSE 异常: error_type=%s error=%s\n%s", type(exc).__name__, exc, traceback.format_exc())
                yield f"data: {json.dumps({'type': 'error', 'content': f'{type(exc).__name__}: {exc}'}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"

        return StreamingResponse(simple_chat_stream(), media_type="text/event-stream")

    # 有文件时走 ReAct Agent 引擎
    if conv_uid not in _engines:
        primary_path = file_paths[0] if file_paths else ""
        primary_name = file_names[0] if file_names else "data.xlsx"
        logger.info("【分支2】创建新 ReactEngine: conv_uid=%s, file=%s, paths=%s", conv_uid, primary_path, file_paths)
        _engines[conv_uid] = ReactEngine(
            conv_uid=conv_uid,
            file_path=primary_path,
            file_name=primary_name,
            file_paths=file_paths,
            file_names=file_names,
            skill_name=req.skill_name,
        )
    else:
        engine = _engines[conv_uid]
        logger.info("【分支3】复用已有引擎: conv_uid=%s, 现有文件列表=%s", conv_uid, engine.file_paths)
        if file_paths:
            for fp, fn in zip(file_paths, file_names):
                if fp and fp not in engine.file_paths:
                    engine.file_paths.append(fp)
                    engine.file_names.append(fn or "data file")
                    logger.info("追加新文件到引擎: %s", fp)

    engine = _engines[conv_uid]

    async def event_stream():
        try:
            conv_exists = await get_conversation(conv_uid)
            if not conv_exists:
                logger.info("创建对话记录: conv_uid=%s", conv_uid)
                await create_conversation(
                    conv_uid=conv_uid,
                    chat_mode="react_agent",
                    model_name=req.model_name,
                    file_path=engine.file_path,
                    file_name=engine.file_name,
                    title=req.user_input[:60] if req.user_input else "",
                )
            final_content = ""
            round_count = 0
            steps = []
            start_time = time.perf_counter()
            logger.info("开始 ReAct Agent 引擎流式分析：conv_uid=%s", conv_uid)
            async for event in engine.run_stream(req.user_input, model_name=req.model_name):
                _apply_react_event(steps, event)
                if event.get("type") == "step.start":
                    round_count += 1
                if event.get("type") == "final":
                    final_content = event.get("content", "")
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            logger.info("ReAct Agent 流式分析结束，共 %d 轮，final_content长度=%d", round_count, len(final_content))
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            await _save_react_round(conv_uid, req.user_input, final_content, steps, elapsed_ms, logger)
            logger.info("ReAct 对话已保存到 DB: conv_uid=%s", conv_uid)
        except Exception as exc:
            logger.error("ReAct SSE 异常: error_type=%s error=%s\n%s", type(exc).__name__, exc, traceback.format_exc())
            yield f"data: {json.dumps({'type': 'error', 'content': f'{type(exc).__name__}: {exc}'}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
