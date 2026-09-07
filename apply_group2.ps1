$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Sovereign AI Workbench - Group 2" -ForegroundColor Cyan
Write-Host " Phase 2: Permissions + Calculator" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$Root = Get-Location

function Write-ProjectFile {
    param(
        [string]$RelativePath,
        [string]$Content
    )

    $Path = Join-Path $Root $RelativePath
    $Directory = Split-Path $Path -Parent

    if (!(Test-Path $Directory)) {
        New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    }

    Set-Content -Path $Path -Value $Content -Encoding UTF8

    Write-Host "Updated: $RelativePath" -ForegroundColor Green
}

# ============================================================
# 1. Tool Registry
# ============================================================

Write-ProjectFile "app/tools/registry.py" @'
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
'@

# ============================================================
# 2. Calculator
# ============================================================

Write-ProjectFile "app/tools/calculator.py" @'
import ast
import operator
from typing import Any


_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


class SafeCalculator:
    """
    Deterministic arithmetic calculator.

    Uses Python AST parsing instead of eval().
    """

    def calculate(
        self,
        expression: str,
    ) -> float | int:

        value, _, _ = self._evaluate(expression)

        return value

    def explain(
        self,
        expression: str,
    ) -> dict[str, Any]:

        value, steps, intermediate_values = (
            self._evaluate(expression)
        )

        return {
            "expression": expression,
            "steps": steps,
            "intermediate_values": intermediate_values,
            "final_result": value,
        }

    def _evaluate(
        self,
        expression: str,
    ) -> tuple[
        float | int,
        list[str],
        list[float | int],
    ]:

        if not expression or not expression.strip():
            raise ValueError(
                "Expression cannot be empty."
            )

        tree = ast.parse(
            expression,
            mode="eval",
        )

        steps: list[str] = []
        intermediate_values: list[float | int] = []

        def visit(node: ast.AST) -> float | int:

            if isinstance(node, ast.Constant):

                if isinstance(
                    node.value,
                    bool,
                ) or not isinstance(
                    node.value,
                    (int, float),
                ):
                    raise ValueError(
                        "Only numeric constants are allowed."
                    )

                return node.value

            if isinstance(
                node,
                ast.UnaryOp,
            ):

                operator_type = type(node.op)

                if operator_type not in _UNARY_OPERATORS:
                    raise ValueError(
                        "Unsupported unary operation."
                    )

                operand = visit(node.operand)

                value = _UNARY_OPERATORS[
                    operator_type
                ](operand)

                steps.append(
                    f"{operand} -> {value}"
                )

                intermediate_values.append(
                    value
                )

                return value

            if isinstance(
                node,
                ast.BinOp,
            ):

                operator_type = type(node.op)

                if operator_type not in _BINARY_OPERATORS:
                    raise ValueError(
                        "Unsupported operation."
                    )

                left = visit(node.left)
                right = visit(node.right)

                try:
                    value = _BINARY_OPERATORS[
                        operator_type
                    ](
                        left,
                        right,
                    )
                except Exception as exc:
                    raise ValueError(
                        str(exc)
                    ) from exc

                symbols = {
                    ast.Add: "+",
                    ast.Sub: "-",
                    ast.Mult: "*",
                    ast.Div: "/",
                    ast.FloorDiv: "//",
                    ast.Mod: "%",
                    ast.Pow: "**",
                }

                symbol = symbols[
                    operator_type
                ]

                steps.append(
                    f"{left} {symbol} {right} = {value}"
                )

                intermediate_values.append(
                    value
                )

                return value

            raise ValueError(
                "Unsupported expression element: "
                f"{type(node).__name__}"
            )

        result = visit(tree.body)

        return (
            result,
            steps,
            intermediate_values,
        )
'@

# ============================================================
# 3. Orchestrator tool registration
# ============================================================

$OrchestratorPath = Join-Path $Root "app\agent\orchestrator.py"

if (!(Test-Path $OrchestratorPath)) {
    throw "Could not find app/agent/orchestrator.py"
}

$orchestrator = Get-Content $OrchestratorPath -Raw

if ($orchestrator -notmatch "ToolCapability") {

    # Add imports.
    $orchestrator = $orchestrator.Replace(
        "from app.tools.registry import ToolRegistry",
        "from app.tools.registry import ToolRegistry, ToolCapability"
    )

    $orchestrator = $orchestrator.Replace(
        "from app.tools.artifact import ArtifactTool",
        "from app.tools.artifact import ArtifactTool`r`nfrom app.tools.workspace import WorkspaceTool"
    )

    # Replace registry construction.
    $orchestrator = $orchestrator.Replace(
        "registry = ToolRegistry()",
        @"
registry = ToolRegistry(
            allowed_capabilities={
                ToolCapability.READ,
                ToolCapability.WRITE,
                ToolCapability.EXECUTE,
            }
        )
"@
    )

    # Add capabilities to existing tools.
    $orchestrator = $orchestrator.Replace(
        "function=calculator.calculate)",
        "function=calculator.calculate, capabilities={ToolCapability.READ})"
    )

    $orchestrator = $orchestrator.Replace(
        "function=vision.execute)",
        "function=vision.execute, capabilities={ToolCapability.READ})"
    )

    $orchestrator = $orchestrator.Replace(
        "function=documents.execute)",
        "function=documents.execute, capabilities={ToolCapability.READ})"
    )

    $orchestrator = $orchestrator.Replace(
        "function=pdf.extract_text)",
        "function=pdf.extract_text, capabilities={ToolCapability.READ})"
    )

    $orchestrator = $orchestrator.Replace(
        "function=python_tool.execute)",
        "function=python_tool.execute, capabilities={ToolCapability.EXECUTE})"
    )

    $orchestrator = $orchestrator.Replace(
        "function=knowledge.execute)",
        "function=knowledge.execute, capabilities={ToolCapability.READ})"
    )

    $orchestrator = $orchestrator.Replace(
        "function=artifact.execute)",
        "function=artifact.execute, capabilities={ToolCapability.WRITE})"
    )

    # Add workspace tools immediately before return registry.
    $workspaceBlock = @"

        workspace = WorkspaceTool()

        registry.register(
            name="read_file",
            description="Reads a file strictly inside the current task workspace.",
            function=workspace.read_file,
            capabilities={ToolCapability.READ},
        )

        registry.register(
            name="write_file",
            description="Writes a file strictly inside the current task workspace.",
            function=workspace.write_file,
            capabilities={ToolCapability.WRITE},
        )

        registry.register(
            name="list_files",
            description="Lists files strictly inside the current task workspace.",
            function=workspace.list_files,
            capabilities={ToolCapability.READ},
        )

        registry.register(
            name="create_directory",
            description="Creates a directory strictly inside the current task workspace.",
            function=workspace.create_directory,
            capabilities={ToolCapability.WRITE},
        )
"@

    $orchestrator = $orchestrator.Replace(
        "        return registry",
        "$workspaceBlock`r`n        return registry"
    )

    Set-Content `
        -Path $OrchestratorPath `
        -Value $orchestrator `
        -Encoding UTF8

    Write-Host "Updated: app/agent/orchestrator.py" -ForegroundColor Green
}
else {
    Write-Host "Orchestrator already contains capability support." -ForegroundColor Yellow
}

# ============================================================
# 4. Group 2 Phase 2 tests
# ============================================================

Write-ProjectFile "tests/test_group2_phase2.py" @'
import pytest

from app.tools.calculator import SafeCalculator
from app.tools.registry import (
    ToolCapability,
    ToolRegistry,
)


def test_registry_success_result():

    registry = ToolRegistry()

    registry.register(
        name="echo",
        description="Echo tool",
        function=lambda value: value,
        capabilities={ToolCapability.READ},
    )

    result = registry.execute(
        "echo",
        value="hello",
    )

    assert result.success is True
    assert result.result == "hello"
    assert result.error is None
    assert result.metadata["tool"] == "echo"


def test_registry_failure_result():

    registry = ToolRegistry()

    def failing_tool():
        raise RuntimeError("intentional failure")

    registry.register(
        name="failure",
        description="Failure tool",
        function=failing_tool,
        capabilities={ToolCapability.EXECUTE},
    )

    result = registry.execute("failure")

    assert result.success is False
    assert result.result is None
    assert "intentional failure" in result.error


def test_network_capability_is_always_denied():

    registry = ToolRegistry(
        allowed_capabilities={
            ToolCapability.READ,
            ToolCapability.WRITE,
            ToolCapability.EXECUTE,
            ToolCapability.NETWORK,
        }
    )

    with pytest.raises(PermissionError):

        registry.register(
            name="network_tool",
            description="Should never be allowed",
            function=lambda: None,
            capabilities={ToolCapability.NETWORK},
        )


def test_read_capability():

    registry = ToolRegistry()

    registry.register(
        name="reader",
        description="Reader",
        function=lambda: "data",
        capabilities={ToolCapability.READ},
    )

    assert registry.has_capability(
        "reader",
        ToolCapability.READ,
    )

    assert not registry.has_capability(
        "reader",
        ToolCapability.WRITE,
    )


def test_calculator_still_returns_scalar():

    calculator = SafeCalculator()

    assert calculator.calculate(
        "15 * 17"
    ) == 255


def test_calculator_explanation():

    calculator = SafeCalculator()

    result = calculator.explain(
        "10 * 5 + 2"
    )

    assert result["expression"] == "10 * 5 + 2"
    assert result["final_result"] == 52
    assert len(result["steps"]) >= 2
    assert len(
        result["intermediate_values"]
    ) >= 2


def test_calculator_rejects_non_math():

    calculator = SafeCalculator()

    with pytest.raises(ValueError):
        calculator.calculate(
            "__import__('os').system('whoami')"
        )
'@

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Phase 2 completed." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Run:"
Write-Host '  $env:PYTHONPATH = (Get-Location).Path'
Write-Host '  python -m pytest -q'
Write-Host ""