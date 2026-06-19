"""模块3 — ReAct Agent 引擎

1:1 复刻自 packages/dbgpt-app/src/dbgpt_app/openapi/api_v1/agentic_data_api.py 的 _react_agent_stream()

核心流程:
  系统提示词 → ReAct循环(thinking→parse→tool→chunks→memory) → SSE推送 → terminate退出

与旧版的关键差异:
- 解析 Action Intention / Action Reason 字段
- terminate 特殊处理: 直接返回 result，不经过 chunks 解析
- todowrite → 推送 plan.update SSE 事件
- 工具输出 chunks → 逐个推送 step.chunk
- 收集 generated_images 供 html_interpreter 使用
- 无效 Action 时自动追加提示让 LLM 重试
- todo 轮次计数兜底:工具成功执行 N 次后自动推进,防 LLM 忘调 todowrite 卡死
"""

import json
import logging
import re
import uuid
from typing import AsyncIterator, Dict, List, Optional

from app.llm.client import chat_completion_full, chat_completion_stream, count_tokens
from app.core.memory import MemoryFragment, ShortTermMemory
from app.core.context import ContextManager
from app.services.react_agent.tools import execute_tool
from app.prompts.react_agent_system import build_react_system_prompt
from app.core.logger import get_session_logger
from app.llm.llm_config import get_default_llm_provider
from app.dal.conversation import get_messages

from app.core import config

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════
# ReAct 输出解析器
# ══════════════════════════════════════════════════════════

def parse_react_output(text: str) -> Dict:
    """解析 LLM 输出的 ReAct 格式 — 1:1 复刻原版

    支持字段: Thought, Action Intention, Action Reason, Action, Action Input
    返回: {
        "thought": "...",
        "action_intention": "...",
        "action_reason": "...",
        "action": "execute_analysis",
        "action_input": {"input_file": "..."}
    }
    """
    result = {
        "thought": "",
        "action_intention": "",
        "action_reason": "",
        "action": "",
        "action_input": {},
    }

    # 提取 Thought
    thought_match = re.search(
        r"Thought:\s*(.*?)(?=\n\s*(?:Action Intention|Action Reason|Action):|$)",
        text, re.DOTALL,
    )
    if thought_match:
        result["thought"] = thought_match.group(1).strip()

    # 提取 Action Intention
    intention_match = re.search(
        r"Action Intention:\s*(.*?)(?=\n\s*(?:Action Reason|Action):|$)",
        text, re.DOTALL,
    )
    if intention_match:
        result["action_intention"] = intention_match.group(1).strip()

    # 提取 Action Reason
    reason_match = re.search(
        r"Action Reason:\s*(.*?)(?=\n\s*Action:|$)",
        text, re.DOTALL,
    )
    if reason_match:
        result["action_reason"] = reason_match.group(1).strip()

    # 提取 Action
    action_match = re.search(r"Action:\s*(\w+)", text)
    if action_match:
        result["action"] = action_match.group(1).strip()

    # 提取 Action Input (JSON) — 用括号计数法只取第一个完整 JSON 对象
    # 避免贪婪正则把模型自带的多轮 Observation/Thought 也包进去
    input_match = re.search(r"Action Input:\s*", text)
    if input_match:
        json_start = input_match.end()
        # 从 json_start 开始用括号计数找第一个平衡的 {...}
        depth = 0
        json_end = -1
        in_string = False
        escape = False
        for i in range(json_start, len(text)):
            ch = text[i]
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    json_end = i + 1
                    break

        if json_end > json_start:
            raw = text[json_start:json_end].strip()
            try:
                result["action_input"] = json.loads(raw)
            except json.JSONDecodeError:
                # 尝试修复常见问题: 末尾多余逗号、缺少闭合括号
                fixed = raw.rstrip()
                if fixed.endswith(","):
                    fixed = fixed[:-1]
                if fixed.count("{") > fixed.count("}"):
                    fixed += "}"
                if fixed.count("[") > fixed.count("]"):
                    fixed += "]"
                try:
                    result["action_input"] = json.loads(fixed)
                except json.JSONDecodeError:
                    result["action_input"] = {"raw": raw}
                    logger.warning("Action Input JSON 解析失败，已 fallback 为 raw: %s", raw[:200])

    return result


# ══════════════════════════════════════════════════════════
# ReactEngine
# ══════════════════════════════════════════════════════════

class ReactEngine:
    """模块3 ReAct Agent 引擎 — 1:1 复刻原版"""

    def __init__(
        self,
        conv_uid: str,
        file_path: str = "",
        file_name: str = "",
        file_paths: list = None,
        file_names: list = None,
        skill_name: str = "",
    ):
        self.conv_uid = conv_uid or uuid.uuid4().hex
        self.file_path = file_path
        self.file_name = file_name or "data.xlsx"
        self.file_paths: List[str] = file_paths or ([file_path] if file_path else [])
        self.file_names: List[str] = file_names or ([file_name] if file_name else [])
        self.skill_name = skill_name
        self.logger = get_session_logger(self.conv_uid, "react_agent")
        self.logger.info("ReactEngine 初始化: conv_uid=%s, file=%s, skill=%s, file_paths=%s",
                         self.conv_uid, file_path, skill_name, file_paths)
        self.memory = ShortTermMemory()
        self.ctx_mgr = ContextManager()
        self.task_progress: List[str] = []
        self.max_retry = config.REACT_MAX_RETRY_COUNT

        # todowrite 状态（可变列表，跨调用保持）
        self._todo_list: List[Dict[str, str]] = []
        # 已生成的图片 URL 列表（供 html_interpreter 引用）
        self._generated_images: List[str] = []
        # 已匹配的 skill（跨调用保持）
        self._matched_skill = None
        # todo 轮次计数兜底：记录当前 in_progress 的 todo 已成功执行的工具次数
        # 达到 _TODO_AUTO_ADVANCE_THRESHOLD 次时自动推进，防止 LLM 忘记调 todowrite 导致进度卡死
        self._todo_tool_count: int = 0
        # 最近一次自动推进的 todo 索引，用于通知 LLM
        self._last_auto_advanced_idx: Optional[int] = None

    # ── todo 轮次计数兜底 ────────────────────────────────────

    _TODO_AUTO_ADVANCE_THRESHOLD = 3

    def _active_todo_index(self) -> Optional[int]:
        """获取当前处于 in_progress 状态的 todo 索引,没有则返回 None"""
        for idx, item in enumerate(self._todo_list):
            if item.get("status") == "in_progress":
                return idx
        return None

    def _record_tool_success(self, action_name: str) -> Optional[int]:
        """记录一次工具成功执行,返回自动推进的 todo 索引(未推进返回 None)

        策略:不猜测 LLM 想干什么,只看它做了什么。
        当 in_progress 的 todo 累计成功执行 N 次工具,自动推进到下一个。
        todowrite 自身不计数(它是更新计划,不是执行任务)。
        """
        if not self._todo_list:
            return None
        if action_name.lower() == "todowrite":
            return None
        active_idx = self._active_todo_index()
        if active_idx is None:
            return None

        self._todo_tool_count += 1
        self.logger.debug("todo 工具计数: idx=%d, count=%d/%d",
                          active_idx, self._todo_tool_count, self._TODO_AUTO_ADVANCE_THRESHOLD)

        if self._todo_tool_count >= self._TODO_AUTO_ADVANCE_THRESHOLD:
            advanced_idx = self._advance_todo_list()
            if advanced_idx is not None:
                self._last_auto_advanced_idx = advanced_idx
                return advanced_idx
        return None

    def _advance_todo_list(self) -> Optional[int]:
        """推进 todo:当前 in_progress 标记 completed,下一个 pending 标记 in_progress

        返回被推进的(原)todo 索引,无变化返回 None。
        """
        active_idx = self._active_todo_index()
        if active_idx is None:
            return None

        self._todo_list[active_idx]["status"] = "completed"
        for next_item in self._todo_list[active_idx + 1:]:
            if next_item.get("status") == "pending":
                next_item["status"] = "in_progress"
                break
        # 重置计数器,新 todo 从 0 开始
        self._todo_tool_count = 0
        return active_idx

    async def _build_conversation_history(self) -> str:
        """从 DB 读取历史消息,提取每轮"用户问题 + finalContent"拼成精简历史

        精简历史只包含结论性文字,不带 ReAct 中间过程,
        避免裸露的 terminate(result=xxx) 触发 LLM 抄答案。
        """
        try:
            history_msgs = await get_messages(self.conv_uid)
        except Exception as e:
            self.logger.warning("读取历史消息失败,跳过精简历史: %s", e)
            return ""

        if not history_msgs:
            return ""

        # 按 order_no 配对: human 问题 + 紧随其后的 ai 消息(含 finalContent)
        lines = []
        i = 0
        while i < len(history_msgs):
            msg = history_msgs[i]
            if msg.get("role") == "human" and msg.get("content"):
                question = msg["content"][:200]  # 截断过长的问题
                # 找紧随其后的 ai 消息
                final_content = ""
                if i + 1 < len(history_msgs) and history_msgs[i + 1].get("role") == "ai":
                    ai_msg = history_msgs[i + 1]
                    metadata_str = ai_msg.get("metadata", "")
                    if metadata_str:
                        try:
                            metadata = json.loads(metadata_str) if isinstance(metadata_str, str) else metadata_str
                            final_content = metadata.get("finalContent", "") or ""
                        except (json.JSONDecodeError, TypeError):
                            pass
                    i += 2  # 跳过 ai 消息
                else:
                    i += 1
                if final_content:
                    final_content = final_content[:500]  # 截断过长的结论
                    lines.append(f"- 用户问: {question}\n  结论: {final_content}")
                else:
                    lines.append(f"- 用户问: {question}\n  结论: (分析未完成)")
            else:
                i += 1

        if not lines:
            return ""

        history_text = "\n".join(lines)
        self.logger.info("精简历史已构建: %d 轮对话", len(lines))
        return history_text

    async def _build_system_prompt(self) -> str:
        """构建系统提示词 — 1:1 复刻原版通用模式

        每轮重新构建,确保 task_progress 始终是最新的。
        task_progress 是所有已完成步骤的摘要,注入 system prompt,
        与 ShortTermMemory(buffer_size=5) 互补:超过5轮后 LLM
        仍能通过 task_progress 掌握全局进展,不会忘记做过什么。
        conversation_history 从 DB finalContent 提取,提供跨问题上下文。
        """
        # 把 task_progress 列表转为带序号的摘要文本
        task_progress_text = ""
        if self.task_progress:
            task_progress_text = "\n".join(
                f"{i+1}. {item}" for i, item in enumerate(self.task_progress)
            )
        # 从 DB 读取精简历史(跨问题上下文)
        conversation_history = await self._build_conversation_history()
        prompt = build_react_system_prompt(
            file_path=self.file_path,
            file_name=self.file_name,
            file_paths=self.file_paths,
            file_names=self.file_names,
            task_progress=task_progress_text,
            skill_name=self.skill_name,
            conversation_history=conversation_history,
        )
        self.logger.info("系统提示词已构建\n%s", prompt)
        return prompt

    async def _load_thinking_messages(self, user_input: str) -> List[dict]:
        """组装 LLM 的 messages 列表（含压缩判断）

        异步方法:L3 压缩需要调 LLM 生成摘要。
        """
        messages = [{"role": "system", "content": await self._build_system_prompt()}]

        # 传入最近 5 轮对话记忆
        memory_msgs = self.memory.read_as_messages()
        messages.extend(memory_msgs)
        self.logger.info("记忆片段: %d 条消息", len(memory_msgs))

        messages.append({"role": "user", "content": user_input})

        messages = await self.ctx_mgr.manage_context(messages, self.memory)
        self.logger.info("Thinking messages 组装完成: 共 %d 条消息", len(messages))
        self.logger.info(
            "\n===== [REACT_THINKING_MESSAGES_FULL] 本轮完整 messages =====\n%s\n===== [REACT_THINKING_MESSAGES_FULL_END] =====\n",
            json.dumps(messages, ensure_ascii=False, indent=2, default=str),
        )

        return messages

    async def run_stream(self, user_input: str) -> AsyncIterator[dict]:
        """ReAct 循环 — yield SSE 事件（主入口）

        SSE 事件格式（1:1 复刻原版，兼容现有前端）:
        - step.start: {type, step, id, title, detail}
        - step.meta: {type, id, thought, action, action_input, action_intention, action_reason}
        - step.chunk: {type, id, output_type, content}
        - plan.update: {type, todos: [...]}
        - step.done: {type, id, status}
        - context.status: {type, used, budget, ratio, state}
        - final: {type, content}
        - done: {type}
        """
        retry_count = 0
        current_input = user_input

        # 每个新用户问题开始独立的 ReAct 循环，清空上一问的 ReAct 轨迹记忆。
        # 避免上一问的 terminate / 最终答案污染当前问题，导致模型复用旧答案。
        # 文件上下文在 system prompt 中始终保留，不依赖短期记忆。
        self.memory.clear()
        self.logger.info("已清空上一问的 ReAct 短期记忆，开始独立分析新问题")

        self.logger.info("===== [REACT_LOOP] 开始 ReAct 循环 =====")
        self.logger.info(
            "\n===== [REACT_USER_INPUT_FULL] 用户原始输入 =====\n%s\n===== [REACT_USER_INPUT_FULL_END] =====\n",
            user_input,
        )

        while retry_count < self.max_retry:
            retry_count += 1
            step_id = f"step_{retry_count}"
            self.logger.info("----- [ROUND %d/%d] -----", retry_count, self.max_retry)
            self.logger.info(
                "\n===== [REACT_ROUND_%d_CURRENT_INPUT_FULL] 当前完整输入 =====\n%s\n===== [REACT_ROUND_%d_CURRENT_INPUT_FULL_END] =====\n",
                retry_count,
                current_input,
                retry_count,
            )

            # ── 1. thinking ──────────────────────────────────────────
            yield {
                "type": "step.start",
                "step": retry_count,
                "id": step_id,
                "title": f"ReAct Round {retry_count}",
                "detail": "",
            }

            messages = await self._load_thinking_messages(current_input)
            yield self.ctx_mgr.get_context_status_event(messages)

            # 调 LLM（流式,实时推送 thought chunk 到前端）
            # 含 L4 reactive_compact:上下文溢出时紧急压缩后重试一次
            llm_output = ""
            llm_succeeded = False
            current_messages = messages
            for llm_attempt in range(2):  # 最多2次:初次 + 压缩后重试1次
                try:
                    self.logger.info("【LLM调用】第%d轮(尝试%d), 消息数=%d",
                                     retry_count, llm_attempt + 1, len(current_messages))
                    if llm_attempt == 0:
                        self.logger.info(
                            "\n===== [REACT_ROUND_%d_LLM_MESSAGES_FULL] 大模型完整输入 messages =====\n%s\n===== [REACT_ROUND_%d_LLM_MESSAGES_FULL_END] =====\n",
                            retry_count,
                            json.dumps(current_messages, ensure_ascii=False, indent=2, default=str),
                            retry_count,
                        )
                    default_llm = get_default_llm_provider()
                    self.logger.info(
                        "LLM 调用参数: stage=react_round_%d, model=%s, temperature=%s, max_tokens=%s, stream=%s, messages=%d",
                        retry_count,
                        default_llm.model,
                        default_llm.temperature,
                        default_llm.max_tokens,
                        True,
                        len(current_messages),
                    )
                    # 流式累积完整输出,同时实时推送 thought chunk
                    llm_output = ""
                    last_pushed_thought = ""
                    async for chunk_text in chat_completion_stream(current_messages):
                        llm_output += chunk_text
                        # 提取到 "Action:" 之前的部分作为 thought 实时推送
                        thought_so_far = re.split(
                            r"\n\s*Action\s*:", llm_output, maxsplit=1
                        )[0]
                        if thought_so_far.startswith("Thought:"):
                            thought_so_far = thought_so_far[len("Thought:"):].strip()
                        # 只在 thought 有变化时推送,避免冗余
                        if thought_so_far and thought_so_far != last_pushed_thought:
                            yield {
                                "type": "step.chunk",
                                "id": step_id,
                                "output_type": "thought",
                                "content": thought_so_far,
                            }
                            last_pushed_thought = thought_so_far

                    self.logger.info("【LLM返回】第%d轮, 长度=%d", retry_count, len(llm_output or ""))
                    self.logger.info(
                        "\n===== [REACT_ROUND_%d_LLM_OUTPUT_FULL] 大模型完整输出 =====\n%s\n===== [REACT_ROUND_%d_LLM_OUTPUT_FULL_END] =====\n",
                        retry_count,
                        llm_output,
                        retry_count,
                    )
                    llm_succeeded = True
                    break  # 成功则跳出重试循环
                except Exception as e:
                    err_str = str(e).lower()
                    # L4: 检测上下文溢出,紧急压缩后重试一次
                    if (
                        llm_attempt == 0
                        and (
                            "context_too_long" in err_str
                            or "context_length_exceeded" in err_str
                            or "maximum context length" in err_str
                        )
                    ):
                        self.logger.warning(
                            "【L4紧急压缩】第%d轮: 检测到上下文溢出(%s),执行 reactive_compact 后重试",
                            retry_count, type(e).__name__,
                        )
                        current_messages = self.ctx_mgr.reactive_compact(current_messages)
                        yield {
                            "type": "step.chunk",
                            "id": step_id,
                            "output_type": "text",
                            "content": "[上下文溢出,已紧急压缩历史消息,正在重试...]",
                        }
                        continue  # 进入第二次循环
                    else:
                        logger.error(f"LLM call failed: {e}")
                        self.logger.error("LLM 调用失败: %s", e)
                        yield {"type": "step.done", "id": step_id, "status": "failed"}
                        yield {"type": "final", "content": f"LLM 调用失败: {str(e)}"}
                        yield {"type": "done"}
                        return

            if not llm_succeeded:
                # 理论上不会走到这里,防御性处理
                yield {"type": "step.done", "id": step_id, "status": "failed"}
                yield {"type": "final", "content": "LLM 调用失败(未知原因)"}
                yield {"type": "done"}
                return

            if not llm_output or not llm_output.strip():
                self.logger.warning("第%d轮: LLM 返回空内容", retry_count)
                yield {
                    "type": "step.chunk",
                    "id": step_id,
                    "output_type": "text",
                    "content": "LLM 返回空内容，重试...",
                }
                yield {"type": "step.done", "id": step_id, "status": "failed"}
                current_input = "请继续执行分析任务。上一步 LLM 返回了空内容。"
                continue

            # ── 2. 解析 ReAct 格式 ───────────────────────────────────
            parsed = parse_react_output(llm_output)
            self.logger.info("【解析结果】第%d轮: action=%s", retry_count, parsed.get("action"))
            self.logger.info(
                "\n===== [REACT_ROUND_%d_PARSED_FULL] 解析后的完整结构 =====\n%s\n===== [REACT_ROUND_%d_PARSED_FULL_END] =====\n",
                retry_count,
                json.dumps(parsed, ensure_ascii=False, indent=2, default=str),
                retry_count,
            )

            # 推送 step.meta
            meta_event = {
                "type": "step.meta",
                "id": step_id,
                "thought": parsed["thought"],
                "action": parsed["action"],
                "action_input": parsed["action_input"],
            }
            if parsed["action_intention"]:
                meta_event["action_intention"] = parsed["action_intention"]
            if parsed["action_reason"]:
                meta_event["action_reason"] = parsed["action_reason"]
            yield meta_event

            # 推送 thought chunk（流式过程已推送,此处跳过避免重复）

            # ── 3. terminate 特殊处理 ────────────────────────────────
            if parsed["action"].lower() == "terminate":
                self.logger.info("【终止】第%d轮: 任务完成", retry_count)
                final_content = parsed["action_input"].get("result", "")
                if not final_content:
                    final_content = parsed["action_input"].get("output", "")
                if not final_content and isinstance(parsed["action_input"], dict):
                    for v in parsed["action_input"].values():
                        if v:
                            final_content = str(v)
                            break
                if not final_content:
                    final_content = parsed["thought"]

                self.memory.write(MemoryFragment(
                    question=current_input,
                    thought=parsed["thought"],
                    action="terminate",
                    action_input=json.dumps(parsed["action_input"], ensure_ascii=False),
                    observation="Task completed",
                ))
                self.task_progress.append(f"完成: {final_content[:100]}")

                # ── terminate 时自动完成所有未完成的 todo ──────────────
                if self._todo_list:
                    for t in self._todo_list:
                        if t["status"] in ("pending", "in_progress"):
                            t["status"] = "completed"
                    yield {"type": "plan.update", "todos": list(self._todo_list)}
                    self.logger.info("【terminate 自动完成 todo】共 %d 个任务已全部标记完成",
                                     len(self._todo_list))

                yield {"type": "step.done", "id": step_id, "status": "done"}
                yield {"type": "final", "content": final_content}
                yield {"type": "done"}
                return

            # ── 4. 无有效 Action → 提示重试 ──────────────────────────
            if not parsed["action"]:
                retry_hint = (
                    "No valid Action found in your response. "
                    "You MUST output in the following format:\n"
                    "Thought: ...\n"
                    "Action Intention: ...\n"
                    "Action Reason: ...\n"
                    "Action: <tool_name>\n"
                    "Action Input: <json>\n"
                    "Please try again."
                )
                yield {
                    "type": "step.chunk",
                    "id": step_id,
                    "output_type": "text",
                    "content": retry_hint,
                }
                yield {"type": "step.done", "id": step_id, "status": "failed"}
                current_input = retry_hint
                continue

            # ── 5. 执行工具 ──────────────────────────────────────────
            self.logger.info("【工具执行】第%d轮: action=%s", retry_count, parsed["action"])
            self.logger.info(
                "\n===== [REACT_ROUND_%d_TOOL_INPUT_FULL] 工具完整输入 =====\n%s\n===== [REACT_ROUND_%d_TOOL_INPUT_FULL_END] =====\n",
                retry_count,
                json.dumps(parsed.get("action_input", {}), ensure_ascii=False, indent=2, default=str),
                retry_count,
            )
            try:
                tool_output = await execute_tool(
                    action=parsed["action"],
                    action_input=parsed["action_input"],
                    file_path=self.file_path,
                    conv_id=self.conv_uid,
                    todo_list_ref=self._todo_list,
                    generated_images=self._generated_images,
                )
                self.logger.info("【工具返回】第%d轮: action=%s, 输出长度=%d",
                                 retry_count, parsed["action"], len(tool_output or ""))
                self.logger.info(
                    "\n===== [REACT_ROUND_%d_TOOL_OUTPUT_FULL] 工具完整输出 =====\n%s\n===== [REACT_ROUND_%d_TOOL_OUTPUT_FULL_END] =====\n",
                    retry_count,
                    tool_output,
                    retry_count,
                )
            except Exception as e:
                tool_output = json.dumps(
                    {"chunks": [{"output_type": "text", "content": f"Tool execution failed: {str(e)}"}]},
                    ensure_ascii=False,
                )
                self.logger.error("工具执行异常: %s", e) 

            # ── 6. 解析工具输出 → 逐 chunk 推送 SSE ─────────────────
            observation_text = ""
            try:
                result = json.loads(tool_output) if isinstance(tool_output, str) else tool_output
            except json.JSONDecodeError:
                result = {"chunks": [{"output_type": "text", "content": tool_output}]}

            chunks = result.get("chunks", [])
            todos = result.get("__todos__")

            # 逐 chunk 推送 step.chunk
            for chunk in chunks:
                output_type = chunk.get("output_type", "text")
                content = chunk.get("content", "")

                yield {
                    "type": "step.chunk",
                    "id": step_id,
                    "output_type": output_type,
                    "content": content,
                }

                # 收集 observation 文本（供记忆使用）
                if output_type == "image":
                    if isinstance(content, str) and content.startswith("/images/"):
                        self._generated_images.append(content)
                    observation_text += f"[Image: {content}]\n"
                elif output_type == "html":
                    observation_text += f"[HTML Report: {chunk.get('title', 'Report')}]\n"
                elif output_type == "code":
                    observation_text += f"```python\n{content}\n```\n"
                elif output_type == "table":
                    rows = content.get("rows", []) if isinstance(content, dict) else []
                    observation_text += f"[Table: {len(rows)} rows]\n"
                elif output_type == "chart":
                    observation_text += "[Chart rendered]\n"
                elif output_type == "json":
                    observation_text += json.dumps(content, ensure_ascii=False) + "\n"
                else:
                    observation_text += str(content) + "\n"

            # 推送 plan.update（如果有 todos）
            if todos:
                self._todo_list.clear()
                self._todo_list.extend(todos)
                yield {"type": "plan.update", "todos": todos}
                self.logger.info("【计划更新】第%d轮: %d 个任务", retry_count, len(todos))

            observation_text = observation_text.strip()
            self.logger.info("【记忆写入】第%d轮: action=%s, observation长度=%d",
                             retry_count, parsed["action"], len(observation_text))
            self.logger.info(
                "\n===== [REACT_ROUND_%d_OBSERVATION_FULL] 写入记忆的完整 Observation =====\n%s\n===== [REACT_ROUND_%d_OBSERVATION_FULL_END] =====\n",
                retry_count,
                observation_text,
                retry_count,
            )

            # ── 7. 写入记忆 ──────────────────────────────────────────
            self.memory.write(MemoryFragment(
                question=current_input if retry_count == 1 else "",
                thought=parsed["thought"],
                action=parsed["action"],
                action_input=json.dumps(parsed["action_input"], ensure_ascii=False),
                observation=observation_text,
            ))

            action_desc = f"{parsed['action']}({json.dumps(parsed['action_input'], ensure_ascii=False)[:50]})"
            self.task_progress.append(action_desc)

            yield {"type": "step.done", "id": step_id, "status": "done"}

            # ── 工具执行成功后:轮次计数兜底推进 todo ─────────────────
            # 策略:不猜 LLM 想干什么,只数成功执行了几次工具。
            # 当前 in_progress 的 todo 累计成功执行 N 次工具后自动推进,
            # 防止 LLM 忘记调 todowrite 导致前端进度条永远卡住。
            # 如果 LLM 已经主动调过 todowrite 更新了状态,计数器会随新 todo 重置。
            advanced_idx = self._record_tool_success(parsed["action"])
            if advanced_idx is not None:
                yield {"type": "plan.update", "todos": list(self._todo_list)}
                done_count = sum(1 for t in self._todo_list if t["status"] == "completed")
                self.logger.info("【轮次计数兜底推进 todo】第%d轮: 任务%d已完成, %d/%d 已完成",
                                 retry_count, advanced_idx + 1, done_count, len(self._todo_list))
                # 在下一轮输入中通知 LLM:这个 todo 被自动标记完成了
                current_input = (
                    f"Observation: {observation_text}\n\n"
                    f"[系统提示] 任务 \"{self._todo_list[advanced_idx].get('content', '')}\" "
                    f"已执行 {self._TODO_AUTO_ADVANCE_THRESHOLD} 次工具,系统自动标记为完成。"
                    f"如尚未完成,请用 todowrite 工具将其状态改回 in_progress。"
                )
            else:
                # 下一轮输入 = Observation
                current_input = f"Observation: {observation_text}"

        # 超过最大轮数
        self.logger.warning("达到最大循环次数 (%d)，无法在轮数内完成", self.max_retry)
        yield {
            "type": "final",
            "content": f"已达到最大循环次数 ({self.max_retry})，分析可能未完成。",
        }
        yield {"type": "done"}
        self.logger.info("===== [REACT_LOOP] ReAct 循环结束（超限） =====")
