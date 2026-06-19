"""沙箱基类 — ExecutionResult, SessionConfig, SandboxSession

复刻自 packages/dbgpt-sandbox/src/dbgpt_sandbox/sandbox/execution_layer/base.py
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ExecutionStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    RESOURCE_LIMIT = "resource_limit"


@dataclass
class ExecutionResult:
    status: ExecutionStatus
    output: str = ""
    error: str = ""
    execution_time: float = 0.0
    memory_usage: int = 0
    exit_code: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "execution_time": self.execution_time,
            "memory_usage": self.memory_usage,
            "exit_code": self.exit_code,
        }


@dataclass
class SessionConfig:
    language: str = "python"
    timeout: int = 30
    max_memory: int = 512 * 1024 * 1024  # 512MB
    working_dir: str = ""
    environment_vars: Dict[str, str] = field(default_factory=dict)


class SandboxSession(ABC):
    def __init__(self, session_id: str, config: SessionConfig):
        self.session_id = session_id
        self.config = config
        self.created_at = time.time()
        self.last_accessed = time.time()
        self._is_active = False

    @property
    def is_active(self) -> bool:
        return self._is_active

    @abstractmethod
    async def start(self) -> bool:
        pass

    @abstractmethod
    async def stop(self) -> bool:
        pass

    @abstractmethod
    async def execute(self, code: str) -> ExecutionResult:
        pass

    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        pass

    def update_last_accessed(self):
        self.last_accessed = time.time()
