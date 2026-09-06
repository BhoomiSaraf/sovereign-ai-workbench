from dataclasses import dataclass
from typing import List

from app.agent.state import AgentState
from app.router.model_router import ModelRouter


@dataclass
class AgentPlan:
    """
    Execution plan for an agent request.
    """

    steps: List[str]


class AgentPlanner:
    """
    Deterministic planner for the MVP.

    The planner decides WHAT needs to happen.
    It does not execute anything.
    """

    def __init__(
        self,
        router: ModelRouter,
    ):
        self.router = router

    def create_plan(
        self,
        state: AgentState,
    ) -> AgentPlan:

        steps = [
            "analyze_task",
            "route_model",
        ]

        if self._requires_knowledge(
            state
        ):
            steps.append(
                "search_knowledge"
            )

        if state.has_image:
            steps.append(
                "analyze_image"
            )

        if self._requires_calculator(
            state.user_input
        ):
            steps.append(
                "calculator"
            )

        steps.append(
            "generate_response"
        )

        return AgentPlan(
            steps=steps
        )

    def _requires_knowledge(
        self,
        state: AgentState,
    ) -> bool:

        text = state.user_input.lower()

        keywords = [
            "according to our",
            "according to the sop",
            "according to the manual",
            "our sop",
            "our policy",
            "company policy",
            "internal policy",
            "internal document",
            "knowledge base",
            "knowledgebase",
            "internal knowledge",
            "organizational",
            "organization's",
        ]

        return any(
            keyword in text
            for keyword in keywords
        )

    def _requires_calculator(
        self,
        text: str,
    ) -> bool:

        text_lower = text.lower()

        keywords = [
            "calculate",
            "compute",
            "what is",
            "how much is",
        ]

        operators = [
            "+",
            "-",
            "*",
            "/",
            "%",
            "**",
        ]

        return (
            any(
                keyword in text_lower
                for keyword in keywords
            )
            and any(
                operator in text
                for operator in operators
            )
        )