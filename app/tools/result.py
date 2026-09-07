from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ToolResult:
    """
    Standard result returned by workbench tools.

    The object also provides limited backward compatibility with the
    project's previous raw dict/scalar tool results.
    """

    success: bool
    result: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Compatibility helper for existing code that previously consumed
        dictionaries returned by tools.
        """

        if key == "success":
            return self.success

        if key == "result":
            return self.result

        if key == "error":
            return self.error

        if key == "metadata":
            return self.metadata

        if isinstance(self.result, dict):
            return self.result.get(key, default)

        return default

    def __getitem__(self, key: str) -> Any:
        value = self.get(key)

        if value is None:
            raise KeyError(key)

        return value

    def __contains__(self, key: str) -> bool:
        if key in {
            "success",
            "result",
            "error",
            "metadata",
        }:
            return True

        return (
            isinstance(self.result, dict)
            and key in self.result
        )

    def __eq__(self, other: Any) -> bool:
        """
        Preserve old behaviour such as:

            registry.execute(...) == 255

        while still exposing the structured ToolResult API.
        """

        if isinstance(other, ToolResult):
            return (
                self.success == other.success
                and self.result == other.result
                and self.error == other.error
                and self.metadata == other.metadata
            )

        return self.result == other

    def __bool__(self) -> bool:
        return self.success

    def __str__(self) -> str:
        if self.result is None:
            return ""

        return str(self.result)