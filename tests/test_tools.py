import pytest

from app.tools.calculator import SafeCalculator, calculate
from app.tools.registry import ToolRegistry


def test_calculator_addition():
    calculator = SafeCalculator()

    assert calculator.calculate("10 + 5") == 15


def test_calculator_multiplication():
    calculator = SafeCalculator()

    assert calculator.calculate("15 * 17") == 255


def test_calculator_parentheses():
    calculator = SafeCalculator()

    assert calculator.calculate(
        "(10 + 5) * 2"
    ) == 30


def test_calculator_power():
    calculator = SafeCalculator()

    assert calculator.calculate(
        "2 ** 8"
    ) == 256


def test_calculator_division():
    calculator = SafeCalculator()

    assert calculator.calculate(
        "100 / 4"
    ) == 25


def test_calculator_rejects_function_calls():
    calculator = SafeCalculator()

    with pytest.raises(ValueError):
        calculator.calculate(
            "__import__('os').system('dir')"
        )


def test_calculator_rejects_non_numeric_values():
    calculator = SafeCalculator()

    with pytest.raises(ValueError):
        calculator.calculate(
            "'hello'"
        )


def test_calculator_rejects_division_by_zero():
    calculator = SafeCalculator()

    with pytest.raises(ValueError):
        calculator.calculate(
            "10 / 0"
        )


def test_calculator_convenience_function():
    assert calculate("20 + 22") == 42


def test_tool_registry_registers_tool():
    registry = ToolRegistry()

    registry.register(
        name="calculator",
        description="Perform arithmetic calculations.",
        function=calculate,
    )

    assert registry.has_tool("calculator")


def test_tool_registry_retrieves_tool():
    registry = ToolRegistry()

    registry.register(
        name="calculator",
        description="Perform arithmetic calculations.",
        function=calculate,
    )

    tool = registry.get("calculator")

    assert tool.name == "calculator"
    assert tool.description == (
        "Perform arithmetic calculations."
    )


def test_tool_registry_executes_tool():
    registry = ToolRegistry()

    registry.register(
        name="calculator",
        description="Perform arithmetic calculations.",
        function=calculate,
    )

    result = registry.execute(
        "calculator",
        expression="15 * 17",
    )

    assert result == 255


def test_tool_registry_rejects_duplicate_tools():
    registry = ToolRegistry()

    registry.register(
        name="calculator",
        description="Perform arithmetic calculations.",
        function=calculate,
    )

    with pytest.raises(ValueError):
        registry.register(
            name="calculator",
            description="Another calculator.",
            function=calculate,
        )


def test_tool_registry_rejects_unknown_tool():
    registry = ToolRegistry()

    with pytest.raises(ValueError):
        registry.get("does_not_exist")