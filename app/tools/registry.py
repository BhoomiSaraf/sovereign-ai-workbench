from dataclasses import dataclass
from typing import Any, Callable, Dict, List


@dataclass
class ToolDefinition:
    """
    Describes a tool available to the agent.
    """

    name: str
    description: str
    function: Callable[..., Any]


class ToolRegistry:
    """
    Registry of tools available to the agent.

    The registry provides a controlled interface for:
        - registering tools
        - discovering tools
        - retrieving tools
        - executing tools
    """

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        function: Callable[..., Any],
    ) -> None:
        """
        Register a tool.
        """

        if name in self._tools:
            raise ValueError(
                f"Tool '{name}' is already registered."
            )

        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            function=function,
        )

    def get(self, name: str) -> ToolDefinition:
        """
        Retrieve a registered tool.
        """

        if name not in self._tools:
            raise ValueError(
                f"Tool '{name}' is not registered."
            )

        return self._tools[name]

    def execute(
        self,
        name: str,
        **kwargs,
    ) -> Any:
        """
        Execute a registered tool.
        """

        tool = self.get(name)

        return tool.function(**kwargs)

    def list_tools(self) -> List[ToolDefinition]:
        """
        Return all registered tools.
        """

        return list(self._tools.values())

    def has_tool(self, name: str) -> bool:
        """
        Check whether a tool is registered.
        """

        return name in self._tools