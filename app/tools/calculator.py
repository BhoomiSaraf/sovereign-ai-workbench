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
def calculate(expression: str) -> float | int:
    """
    Backward-compatible module-level calculator function.
    """
    return SafeCalculator().calculate(expression)