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
