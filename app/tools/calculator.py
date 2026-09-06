import ast
import operator


class SafeCalculator:
    """
    Safe arithmetic calculator.

    Uses Python's AST parser instead of eval(), and only permits
    explicitly supported arithmetic operations.
    """

    _OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def calculate(self, expression: str) -> float:
        """
        Evaluate a mathematical expression safely.

        Supported:
            +, -, *, /, //, %, **
            parentheses
            positive/negative numbers

        Examples:
            15 * 17
            (100 + 50) / 5
            2 ** 8
        """

        if not expression or not expression.strip():
            raise ValueError(
                "Expression cannot be empty."
            )

        try:
            tree = ast.parse(
                expression,
                mode="eval",
            )
        except SyntaxError as exc:
            raise ValueError(
                "Invalid mathematical expression."
            ) from exc

        return self._evaluate(tree.body)

    def _evaluate(self, node):
        """
        Recursively evaluate an allowed AST node.
        """

        if isinstance(node, ast.Constant):

            if isinstance(node.value, bool):
                raise ValueError(
                    "Boolean values are not supported."
                )

            if isinstance(
                node.value,
                (int, float),
            ):
                return node.value

            raise ValueError(
                "Only numeric values are supported."
            )

        if isinstance(
            node,
            ast.BinOp,
        ):
            operator_function = self._OPERATORS.get(
                type(node.op)
            )

            if operator_function is None:
                raise ValueError(
                    "Unsupported arithmetic operator."
                )

            left = self._evaluate(node.left)
            right = self._evaluate(node.right)

            try:
                return operator_function(
                    left,
                    right,
                )
            except ZeroDivisionError as exc:
                raise ValueError(
                    "Division by zero is not allowed."
                ) from exc
            except (OverflowError, ValueError) as exc:
                raise ValueError(
                    "Invalid arithmetic operation."
                ) from exc

        if isinstance(
            node,
            ast.UnaryOp,
        ):
            operator_function = self._OPERATORS.get(
                type(node.op)
            )

            if operator_function is None:
                raise ValueError(
                    "Unsupported unary operator."
                )

            value = self._evaluate(node.operand)

            return operator_function(value)

        raise ValueError(
            "Only arithmetic expressions are allowed."
        )


_calculator = SafeCalculator()


def calculate(expression: str) -> float:
    """
    Convenience function used by the tool registry.
    """

    return _calculator.calculate(expression)
