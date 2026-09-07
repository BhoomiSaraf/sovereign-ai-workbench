from app.security.sandbox import PythonSandbox
from app.tools.result import ToolResult


class PythonTool:

    name = "python"

    def __init__(
        self,
        sandbox=None,
    ):
        self.sandbox = (
            sandbox
            or PythonSandbox()
        )

    def execute(
        self,
        code: str,
        task_id: str | None = None,
        workspace_root: str | None = None,
    ) -> ToolResult:

        try:

            result = self.sandbox.execute(
                code,
                workspace_root=workspace_root,
            )

            return ToolResult(
                success=result.success,
                result=result.stdout,
                error=(
                    result.stderr
                    if not result.success
                    else None
                ),
                metadata={
                    "return_code": result.return_code,
                    "timed_out": result.timed_out,
                    "task_id": task_id,
                    "workspace_root": workspace_root,
                    "stderr": result.stderr,
                    "stdout": result.stdout,
                },
            )

        except Exception as exc:

            return ToolResult(
                success=False,
                result=None,
                error=str(exc),
                metadata={
                    "task_id": task_id,
                    "workspace_root": workspace_root,
                },
            )


class _PythonReplCompatibility:

    def __init__(
        self,
        tool=None,
    ):
        self.tool = tool or PythonTool()

    def invoke(
        self,
        payload,
    ):
        result = self.tool.execute(
            payload.get("code", "")
        )

        if result.success:
            return result.result or ""

        return result.error or ""


python_repl = _PythonReplCompatibility()
