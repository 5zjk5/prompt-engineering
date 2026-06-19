"""ShortTermMemory — 进程内存，只保留最近 N 条记忆片段

复刻自 DB-GPT 的 AgentMemory → ShortTermMemory(buffer_size=5)
"""

from typing import List, Optional
from dataclasses import dataclass

from app.core import config


@dataclass
class MemoryFragment:
    """一条记忆片段 — 对应一轮 ReAct 循环"""
    question: str = ""
    thought: str = ""
    action: str = ""
    action_input: str = ""
    observation: str = ""

    def to_text(self) -> str:
        parts = []
        if self.question:
            parts.append(f"Question: {self.question}")
        if self.thought:
            parts.append(f"Thought: {self.thought}")
        if self.action:
            parts.append(f"Action: {self.action}")
        if self.action_input:
            parts.append(f"Action Input: {self.action_input}")
        if self.observation:
            parts.append(f"Observation: {self.observation}")
        return "\n".join(parts)


class ShortTermMemory:
    """短期记忆 — 只保留最近 buffer_size 条"""

    def __init__(self, buffer_size: int = None):
        self.buffer_size = buffer_size or config.SHORT_TERM_MEMORY_BUFFER_SIZE
        self._buffer: List[MemoryFragment] = []

    def write(self, fragment: MemoryFragment):
        self._buffer.append(fragment)
        if len(self._buffer) > self.buffer_size:
            self._buffer.pop(0)

    def read(self) -> List[MemoryFragment]:
        return list(self._buffer)

    def read_as_messages(self) -> List[dict]:
        """将记忆转为 LLM messages 格式（每条片段作为一条 HumanMessage）"""
        messages = []
        for frag in self._buffer:
            text = frag.to_text()
            if text:
                messages.append({"role": "user", "content": text})
        return messages

    def clear(self):
        self._buffer.clear()

    def __len__(self):
        return len(self._buffer)
