from app.security.workspace import TaskWorkspace
from app.tools.result import ToolResult


class WorkspaceTool:

    def _get_workspace(
        self,
        task_id: str,
        workspace_root: str | None = None,
    ) -> TaskWorkspace:

        if workspace_root:
            return TaskWorkspace(
                task_id=task_id,
                root=workspace_root,
            )

        return TaskWorkspace(task_id=task_id)

    def read_file(
        self,
        task_id: str,
        path: str,
        workspace_root: str | None = None,
    ) -> ToolResult:

        try:
            workspace = self._get_workspace(
                task_id,
                workspace_root,
            )

            content = workspace.read_file(path)

            return ToolResult(
                success=True,
                result=content,
                metadata={
                    "operation": "read_file",
                    "path": path,
                },
            )

        except Exception as exc:
            return ToolResult(
                success=False,
                error=str(exc),
                metadata={
                    "operation": "read_file",
                    "path": path,
                },
            )

    def write_file(
        self,
        task_id: str,
        path: str,
        content: str,
        workspace_root: str | None = None,
    ) -> ToolResult:

        try:
            workspace = self._get_workspace(
                task_id,
                workspace_root,
            )

            written = workspace.write_file(
                path,
                content,
            )

            return ToolResult(
                success=True,
                result=written,
                metadata={
                    "operation": "write_file",
                    "path": path,
                },
            )

        except Exception as exc:
            return ToolResult(
                success=False,
                error=str(exc),
                metadata={
                    "operation": "write_file",
                    "path": path,
                },
            )

    def list_files(
        self,
        task_id: str,
        path: str = ".",
        workspace_root: str | None = None,
    ) -> ToolResult:

        try:
            workspace = self._get_workspace(
                task_id,
                workspace_root,
            )

            files = workspace.list_files(path)

            return ToolResult(
                success=True,
                result=files,
                metadata={
                    "operation": "list_files",
                    "path": path,
                },
            )

        except Exception as exc:
            return ToolResult(
                success=False,
                error=str(exc),
                metadata={
                    "operation": "list_files",
                    "path": path,
                },
            )

    def create_directory(
        self,
        task_id: str,
        path: str,
        workspace_root: str | None = None,
    ) -> ToolResult:

        try:
            workspace = self._get_workspace(
                task_id,
                workspace_root,
            )

            created = workspace.create_directory(path)

            return ToolResult(
                success=True,
                result=created,
                metadata={
                    "operation": "create_directory",
                    "path": path,
                },
            )

        except Exception as exc:
            return ToolResult(
                success=False,
                error=str(exc),
                metadata={
                    "operation": "create_directory",
                    "path": path,
                },
            )
