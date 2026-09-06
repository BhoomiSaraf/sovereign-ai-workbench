from dataclasses import dataclass
from typing import Any, Dict, List

from app.agent.state import AgentState
from app.router.model_router import ModelRouter


@dataclass
class AgentPlan:
    """
    Execution plan for an agent request.

    The planner decides WHAT needs to happen.
    It does not execute anything.
    """

    steps: List[str]
    requirements: Dict[str, Any]


class AgentPlanner:
    """
    Deterministic planner for the MVP.

    The planner converts the user request and current state
    into explicit execution requirements.
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

        requirements = self._analyze_requirements(state)

        steps = [
            "analyze_task",
            "route_model",
        ]

        if requirements["document_required"]:
            steps.append("process_document")

        if requirements["vision_required"]:
            steps.append("analyze_image")

        if requirements["rag_required"]:
            steps.append("search_knowledge")

        if requirements["calculator_required"]:
            steps.append("calculator")

        if requirements["python_required"]:
            steps.append("python")

        steps.append("generate_response")

        if requirements["artifact_required"]:
            steps.append("generate_artifact")

        return AgentPlan(
            steps=steps,
            requirements=requirements,
        )

    def _analyze_requirements(
        self,
        state: AgentState,
    ) -> Dict[str, Any]:

        text = state.user_input.lower()

        document_required = bool(
            state.metadata.get("file_path")
            or state.metadata.get("document_path")
        )

        vision_required = bool(
            state.has_image
            or document_required
        )

        rag_required = self._requires_knowledge(
            state
        )

        calculator_required = self._requires_calculator(
            state.user_input
        )

        python_required = self._requires_python(
            state.user_input
        )

        artifact_required = self._requires_artifact(
            state.user_input
        )

        return {
            "document_required": document_required,
            "vision_required": vision_required,
            "rag_required": rag_required,
            "calculator_required": calculator_required,
            "python_required": python_required,
            "artifact_required": artifact_required,
            "artifact_type": (
                "docx"
                if artifact_required
                else None
            ),
            "reasoning_required": True,
        }

    def _requires_knowledge(
        self,
        state: AgentState,
    ) -> bool:

        text = state.user_input.lower()

        explicit_reference_phrases = [
            "according to",
            "as per",
            "based on the sop",
            "based on our",
            "refer to the sop",
            "refer to our",
            "check the sop",
            "check our",
            "our policy",
            "company policy",
            "internal policy",
            "internal document",
            "internal knowledge",
            "knowledge base",
            "knowledgebase",
            "organizational",
            "organization's",
        ]

        return any(
            phrase in text
            for phrase in explicit_reference_phrases
        )

    def _requires_calculator(
        self,
        text: str,
    ) -> bool:

        text_lower = text.lower()

        calculation_terms = [
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
                term in text_lower
                for term in calculation_terms
            )
            and any(
                operator in text
                for operator in operators
            )
        )

    def _requires_python(
        self,
        text: str,
    ) -> bool:

        text_lower = text.lower()

        execution_terms = [
            "run code",
            "execute code",
            "test code",
            "debug code",
            "run this",
            "execute this",
            "unit test",
        ]

        return any(
            term in text_lower
            for term in execution_terms
        )

    def _requires_artifact(
        self,
        text: str,
    ) -> bool:

        text_lower = text.lower()

        artifact_terms = [
            "approval note",
            "approval memo",
            "approval document",
            "prepare a note",
            "prepare a memo",
            "prepare a report",
            "generate a report",
            "generate a document",
            "create a report",
            "create a document",
            "draft a report",
            "draft a document",
            "write an approval",
        ]

        return any(
            term in text_lower
            for term in artifact_terms
        )