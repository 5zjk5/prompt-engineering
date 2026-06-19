"""4层上下文压缩管理器

复刻自 DB-GPT 的 ContextManager + compact.py
L1: ObservationMicroCompact — 截断旧 Observation
L2: SessionMemoryCompact — 丢弃旧轮次（保留最近3轮）
L3: FullContextCompression — LLM 摘要
L4: ReactiveCompact — 紧急模式，只保留最近2轮
"""

import logging
from typing import List

from app.llm.client import chat_completion_full, count_tokens
from app.core.memory import MemoryFragment, ShortTermMemory

from app.core import config

logger = logging.getLogger(__name__)


class ContextBudgetConfig:
    def __init__(self):
        self.max_context_tokens = config.CONTEXT_MAX_TOKENS
        self.reserved_tokens = config.CONTEXT_RESERVED_TOKENS
        self.warning_threshold = config.CONTEXT_WARNING_THRESHOLD
        self.error_threshold = config.CONTEXT_ERROR_THRESHOLD

    @property
    def effective_budget(self) -> int:
        return self.max_context_tokens - self.reserved_tokens


class ContextManager:
    """上下文管理器 — 管理 token 预算和压缩"""

    def __init__(self):
        self.budget = ContextBudgetConfig()

    def count_messages_tokens(self, messages: list) -> int:
        total = 0
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                total += count_tokens(content)
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, str):
                        total += count_tokens(part)
                    elif isinstance(part, dict):
                        total += count_tokens(str(part))
        return total

    def get_context_state(self, messages: list) -> str:
        """返回当前上下文状态: normal / warning / error / overflow"""
        used = self.count_messages_tokens(messages)
        budget = self.budget.effective_budget
        if budget <= 0:
            return "overflow"
        ratio = used / budget
        if ratio < self.budget.warning_threshold:
            return "normal"
        elif ratio < self.budget.error_threshold:
            return "warning"
        elif ratio < 1.0:
            return "error"
        else:
            return "overflow"

    async def manage_context(self, messages: list, memory: ShortTermMemory) -> list:
        """根据 token 占用率执行压缩，返回压缩后的 messages

        L3 需要调 LLM 生成摘要,故为异步方法。
        """
        state = self.get_context_state(messages)

        if state == "normal":
            return messages

        logger.info(f"Context state: {state}, applying compression...")

        # L1: 截断旧 Observation
        messages = self._layer1_truncate_observations(messages, memory)

        if state in ("warning", "error", "overflow"):
            # L2: 丢弃旧轮次
            messages = self._layer2_drop_old_rounds(messages)

        if state in ("error", "overflow"):
            # L3: LLM 摘要,把旧消息替换为1条摘要消息
            messages = await self._layer3_summary(messages)

        return messages

    def _layer1_truncate_observations(self, messages: list, memory: ShortTermMemory) -> list:
        """L1: 截断旧的 Observation 内容"""
        truncated = []
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str) and "Observation:" in content:
                # 截断到 500 字符
                if len(content) > 500:
                    truncated_content = content[:500] + "\n... (truncated)"
                    truncated.append({**msg, "content": truncated_content})
                    continue
            truncated.append(msg)
        return truncated

    def _layer2_drop_old_rounds(self, messages: list) -> list:
        """L2: 只保留最近 3 轮对话"""
        # 保留 system 消息 + 最近 3 轮
        system_msgs = [m for m in messages if m.get("role") == "system"]
        other_msgs = [m for m in messages if m.get("role") != "system"]

        # 每轮约 2 条消息（user + assistant），3 轮 = 6 条
        keep_count = min(len(other_msgs), 6)
        kept = other_msgs[-keep_count:]

        return system_msgs + kept

    async def _layer3_summary(self, messages: list) -> list:
        """L3: 调 LLM 对旧消息生成结构化摘要,替换为1条摘要消息

        复刻原版 FullContextCompression 的行为:
        保留 system 消息 + 最近 2 轮,把更早的消息交给 LLM 生成摘要,
        摘要作为1条 user 消息插入到最近轮次之前。
        """
        system_msgs = [m for m in messages if m.get("role") == "system"]
        other_msgs = [m for m in messages if m.get("role") != "system"]

        # 保留最近 2 轮(约 4 条消息)
        keep_count = min(len(other_msgs), 4)
        kept = other_msgs[-keep_count:] if keep_count > 0 else []
        to_summarize = other_msgs[:-keep_count] if keep_count > 0 else other_msgs

        if not to_summarize:
            return system_msgs + kept

        # 构建摘要请求:把要压缩的消息拼成文本,让 LLM 生成简洁摘要
        summary_input = "\n".join(
            f"[{m.get('role', 'user')}]: {m.get('content', '')[:500]}"
            for m in to_summarize
        )
        summary_prompt = [
            {"role": "system", "content": "你是一个对话摘要助手。请把以下多轮对话历史压缩为一段简洁的中文摘要,保留关键信息:做过什么分析、得到什么结论、生成了什么文件。不要丢失重要的事实和数值。"},
            {"role": "user", "content": summary_input},
        ]

        try:
            summary_text = await chat_completion_full(
                summary_prompt,
                temperature=0.3,
                max_tokens=800,
            )
            logger.info("L3 摘要生成成功: 原始%d条消息 → 摘要%d字符",
                        len(to_summarize), len(summary_text or ""))
        except Exception as e:
            # 摘要失败时降级为截断,不阻断主流程
            logger.warning("L3 摘要生成失败,降级为截断: %s", e)
            return system_msgs + kept

        summary_msg = {
            "role": "user",
            "content": f"[历史对话摘要]\n{summary_text}",
        }
        return system_msgs + [summary_msg] + kept

    def reactive_compact(self, messages: list) -> list:
        """L4: 紧急模式 — 只保留 system + 最近 1 轮"""
        system_msgs = [m for m in messages if m.get("role") == "system"]
        other_msgs = [m for m in messages if m.get("role") != "system"]
        keep_count = min(len(other_msgs), 2)
        kept = other_msgs[-keep_count:]
        return system_msgs + kept

    def get_context_status_event(self, messages: list) -> dict:
        """生成 context.status SSE 事件"""
        used = self.count_messages_tokens(messages)
        budget = self.budget.effective_budget
        ratio = round(used / budget, 4) if budget > 0 else 1.0
        state = self.get_context_state(messages)
        return {
            "type": "context.status",
            "used": used,
            "budget": budget,
            "ratio": ratio,
            "state": state,
        }
