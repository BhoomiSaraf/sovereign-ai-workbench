from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from app.tools.result import ToolResult


class ToolCapability(str, Enum):
    READ = "READ"
    WRITE = "WRITE"
    EXECUTE = "EXECUTE"
    NETWORK = "NETWORK"


@dataclass
class ToolDefinition:
    name: str
    description: str
    function: Callable[..., Any]
    capabilities: set[ToolCapability] = field(default_factory=set)
    enabled: bool = True


class ToolRegistry:
    """
    Registry for local tools.

    NETWORK is explicitly prohibited for the sovereign workbench.
    """

    def __init__(
        self,
        allowed_capabilities: Optional[set[ToolCapability]] = None,
    ):
        if allowed_capabilities is None:
            allowed_capabilities = {
                ToolCapability.READ,
                ToolCapability.WRITE,
                ToolCapability.EXECUTE,
            }

        self.allowed_capabilities = set(allowed_capabilities)

        # Air-gapped policy:
        self.allowed_capabilities.discard(
            ToolCapability.NETWORK
        )

        self._tools: Dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        function: Callable[..., Any],
        capabilities: Optional[set[ToolCapability]] = None,
    ) -> None:

        if name in self._tools:
            raise ValueError(
                f"Tool already registered: {name}"
            )

        caps = set(capabilities or set())

        if ToolCapability.NETWORK in caps:
            raise PermissionError(
                "NETWORK capability is prohibited "
                "in Sovereign AI Workbench."
            )

        denied = caps - self.allowed_capabilities

        if denied:
            raise PermissionError(
                f"Tool '{name}' requests denied capabilities: "
                f"{sorted(cap.value for cap in denied)}"
            )

        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            function=function,
            capabilities=caps,
        )

    def get(self, name: str) -> ToolDefinition:
        if name not in self._tools:
            raise ValueError(
                f"Unknown tool: {name}"
            )

        tool = self._tools[name]

        if not tool.enabled:
            raise PermissionError(
                f"Tool is disabled: {name}"
            )

        return tool

    def execute(
        self,
        name: str,
        **kwargs: Any,
    ) -> ToolResult:

        try:
            tool = self.get(name)

            value = tool.function(**kwargs)

            if isinstance(value, ToolResult):
                return value

            return ToolResult(
                success=True,
                result=value,
                error=None,
                metadata={
                    "tool": name,
                    "capabilities": sorted(
                        capability.value
                        for capability in tool.capabilities
                    ),
                },
            )

        except Exception as exc:
            return ToolResult(
                success=False,
                result=None,
                error=str(exc),
                metadata={
                    "tool": name,
                },
            )

    def list_tools(self) -> List[ToolDefinition]:
        return list(self._tools.values())

    def has_tool(self, name: str) -> bool:
        return name in self._tools

    def capabilities(
        self,
        name: str,
    ) -> set[ToolCapability]:

        return set(
            self.get(name).capabilities
        )

    def has_capability(
        self,
        name: str,
        capability: ToolCapability,
    ) -> bool:

        return capability in self.capabilities(name)
