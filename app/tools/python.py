from __future__ import annotations

from app.security.sandbox import PythonSandbox


class PythonTool:
    name = "python"

    def __init__(self, sandbox: PythonSandbox | None = None):
        self.sandbox = sandbox or PythonSandbox()

    def execute(self, code: str) -> dict:
        result = self.sandbox.execute(code)

        return {
            "success": result.success,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.return_code,
            "timed_out": result.timed_out,
        }