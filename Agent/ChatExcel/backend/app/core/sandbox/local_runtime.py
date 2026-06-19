"""本地进程沙箱 — subprocess + 资源限制

复刻自 packages/dbgpt-sandbox/src/dbgpt_sandbox/sandbox/execution_layer/local_runtime.py
精简: 只保留 Python 执行，去掉多语言支持。
"""

import asyncio
import os
import shutil
import subprocess
import tempfile
import time
from typing import Any, Dict, List, Optional

import psutil

from app.core.sandbox.base import ExecutionResult, ExecutionStatus, SandboxSession, SessionConfig

from app.core import config


# ── 安全工具 ──────────────────────────────────────────────

class SecurityUtils:
    DANGEROUS_PATTERNS = [
        ("import os", "os 模块"),
        ("import subprocess", "subprocess 模块"),
        ("__import__", "动态导入"),
        ("eval(", "eval 函数"),
        ("exec(", "exec 函数"),
        ("rm -rf", "递归删除"),
        ("os.system(", "系统命令"),
        ("os.popen(", "管道命令"),
    ]

    @staticmethod
    def validate_code(code: str) -> List[str]:
        warnings = []
        code_lower = code.lower()
        for pattern, desc in SecurityUtils.DANGEROUS_PATTERNS:
            if pattern.lower() in code_lower:
                warnings.append(f"检测到潜在危险操作: {desc} ({pattern})")
        return warnings


# ── 进程管理 ──────────────────────────────────────────────

class ProcessManager:
    @staticmethod
    def kill_process_tree(pid: int) -> bool:
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
            gone, alive = psutil.wait_procs(children, timeout=3)
            for p in alive:
                try:
                    p.kill()
                except psutil.NoSuchProcess:
                    pass
            try:
                parent.terminate()
                parent.wait(timeout=3)
            except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                try:
                    parent.kill()
                except psutil.NoSuchProcess:
                    pass
            return True
        except Exception as e:
            print(f"Kill process tree failed: {e}")
            return False


# ── 本地沙箱会话 ─────────────────────────────────────────

class LocalSandboxSession(SandboxSession):
    def __init__(self, session_id: str, config: SessionConfig):
        super().__init__(session_id, config)
        self.work_dir: Optional[str] = None
        self.process_pool: List[int] = []

    async def start(self) -> bool:
        try:
            if self.config.working_dir and os.path.isabs(self.config.working_dir):
                os.makedirs(self.config.working_dir, exist_ok=True)
                self.work_dir = self.config.working_dir
            else:
                self.work_dir = tempfile.mkdtemp(prefix=f"sandbox_{self.session_id}_")

            self._is_active = True
            return True
        except Exception as e:
            print(f"Start sandbox failed: {e}")
            return False

    async def stop(self) -> bool:
        try:
            for pid in self.process_pool:
                ProcessManager.kill_process_tree(pid)
            if self.work_dir and os.path.exists(self.work_dir):
                shutil.rmtree(self.work_dir, ignore_errors=True)
            self._is_active = False
            return True
        except Exception as e:
            print(f"Stop sandbox failed: {e}")
            return False

    async def execute(self, code: str) -> ExecutionResult:
        if not self._is_active or not self.work_dir:
            return ExecutionResult(status=ExecutionStatus.ERROR, error="会话未启动")

        self.update_last_accessed()

        # 安全检查（仅警告，不阻止执行）
        warnings = SecurityUtils.validate_code(code)
        if warnings:
            # 在生产环境可以改为阻止执行
            pass

        code_file = None
        try:
            # 写入临时 Python 文件
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", dir=self.work_dir, delete=False, encoding="utf-8"
            ) as f:
                f.write(code)
                code_file = f.name

            start_time = time.time()
            result = await self._run_with_limits(["python", code_file])
            execution_time = time.time() - start_time

            # 截断输出
            output = result["stdout"]
            if len(output) > config.SANDBOX_MAX_OUTPUT_CHARS:
                output = output[:config.SANDBOX_MAX_OUTPUT_CHARS] + "\n... (output truncated)"

            return ExecutionResult(
                status=ExecutionStatus.SUCCESS if result["returncode"] == 0 else ExecutionStatus.ERROR,
                output=output,
                error=result["stderr"],
                execution_time=execution_time,
                exit_code=result["returncode"],
            )

        except asyncio.TimeoutError:
            return ExecutionResult(
                status=ExecutionStatus.TIMEOUT,
                error=f"执行超时 ({self.config.timeout}秒)",
            )
        except Exception as e:
            return ExecutionResult(
                status=ExecutionStatus.ERROR, error=f"执行失败: {str(e)}"
            )
        finally:
            if code_file and os.path.exists(code_file):
                os.unlink(code_file)

    async def _run_with_limits(self, command: List[str]) -> Dict[str, Any]:
        process = None
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.work_dir,
                env=dict(os.environ, **self.config.environment_vars),
            )

            if process.pid:
                self.process_pool.append(process.pid)

            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=self.config.timeout
            )

            if process.pid in self.process_pool:
                self.process_pool.remove(process.pid)

            return {
                "returncode": process.returncode,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
            }

        except asyncio.TimeoutError:
            if process and process.pid:
                ProcessManager.kill_process_tree(process.pid)
                if process.pid in self.process_pool:
                    self.process_pool.remove(process.pid)
            raise
        except Exception as e:
            if process and process.pid:
                ProcessManager.kill_process_tree(process.pid)
                if process.pid in self.process_pool:
                    self.process_pool.remove(process.pid)
            raise

    async def get_status(self) -> Dict[str, Any]:
        if not self._is_active:
            return {"status": "stopped"}
        return {
            "status": "running",
            "work_dir": self.work_dir,
            "process_count": len(self.process_pool),
        }


# ── 本地运行时 ───────────────────────────────────────────

class LocalRuntime:
    def __init__(self):
        self.sessions: Dict[str, LocalSandboxSession] = {}

    async def create_session(self, session_id: str, config: SessionConfig) -> LocalSandboxSession:
        if session_id in self.sessions:
            raise ValueError(f"会话 {session_id} 已存在")
        session = LocalSandboxSession(session_id, config)
        if await session.start():
            self.sessions[session_id] = session
            return session
        raise RuntimeError(f"启动会话 {session_id} 失败")

    async def destroy_session(self, session_id: str) -> bool:
        if session_id not in self.sessions:
            return False
        session = self.sessions[session_id]
        success = await session.stop()
        if success:
            del self.sessions[session_id]
        return success

    async def get_session(self, session_id: str) -> Optional[LocalSandboxSession]:
        return self.sessions.get(session_id)
