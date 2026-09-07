from pathlib import Path
import re


_TASK_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


class WorkspaceSecurityError(ValueError):
    """Raised when a path attempts to escape the task workspace."""


class TaskWorkspace:
    """
    Secure filesystem boundary for a single agent task.

    All operations are restricted to:

        workspace/tasks/<task_id>/
    """

    def __init__(
        self,
        task_id: str,
        root: str | Path = "workspace/tasks",
    ):
        if not task_id:
            raise WorkspaceSecurityError("task_id cannot be empty.")

        if not _TASK_ID_PATTERN.fullmatch(task_id):
            raise WorkspaceSecurityError(
                "Invalid task_id. Only letters, numbers, '_' and '-' are allowed."
            )

        self.tasks_root = Path(root).resolve()
        self.root = (self.tasks_root / task_id).resolve()

        self.tasks_root.mkdir(parents=True, exist_ok=True)
        self.root.mkdir(parents=True, exist_ok=True)

        try:
            self.root.relative_to(self.tasks_root)
        except ValueError as exc:
            raise WorkspaceSecurityError(
                "Task workspace escaped the workspace root."
            ) from exc

    def resolve(self, relative_path: str | Path = ".") -> Path:
        if relative_path is None:
            raise WorkspaceSecurityError("Path cannot be None.")

        value = str(relative_path)

        if not value.strip():
            value = "."

        candidate = Path(value)

        if candidate.is_absolute():
            raise WorkspaceSecurityError(
                "Absolute paths are not permitted."
            )

        if len(value) >= 2 and value[1] == ":":
            raise WorkspaceSecurityError(
                "Drive-qualified paths are not permitted."
            )

        resolved = (self.root / candidate).resolve()

        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise WorkspaceSecurityError(
                "Path escapes the task workspace."
            ) from exc

        return resolved

    def read_file(self, relative_path: str) -> str:
        path = self.resolve(relative_path)

        if not path.exists():
            raise FileNotFoundError(relative_path)

        if not path.is_file():
            raise IsADirectoryError(relative_path)

        return path.read_text(encoding="utf-8")

    def write_file(
        self,
        relative_path: str,
        content: str,
    ) -> str:
        path = self.resolve(relative_path)

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

        return str(path.relative_to(self.root))

    def create_directory(
        self,
        relative_path: str,
    ) -> str:
        path = self.resolve(relative_path)

        path.mkdir(parents=True, exist_ok=True)

        return str(path.relative_to(self.root))

    def list_files(
        self,
        relative_path: str = ".",
    ) -> list[str]:
        directory = self.resolve(relative_path)

        if not directory.exists():
            raise FileNotFoundError(relative_path)

        if not directory.is_dir():
            raise NotADirectoryError(relative_path)

        return sorted(
            str(path.relative_to(self.root))
            for path in directory.rglob("*")
            if path.is_file()
        )
