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


class _PythonRepl:
    """
    Compatibility interface for callers expecting a tool with
    an .invoke({"code": ...}) method.

    Execution still uses the existing PythonTool and PythonSandbox.
    """

    def invoke(self, arguments: dict) -> str:
        code = arguments.get("code")

        if not code:
            raise ValueError("code is required.")

        result = PythonTool().execute(code)

        if result["success"]:
            return result["stdout"]

        return result["stderr"] or (
            f"Execution failed with return code "
            f"{result['return_code']}"
        )


python_repl = _PythonRepl()