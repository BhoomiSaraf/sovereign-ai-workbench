from dataclasses import dataclass, field
from typing import List

from app.agent.state import AgentState


@dataclass
class ToolSelection:
    tools: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)


class ToolSelector:
    """
    Selects local tools required to execute an agent task.

    Explicit requirements produced by the planner take priority.
    Lightweight state-based fallbacks are retained for direct
    execution compatibility.
    """

    def select(
        self,
        state: AgentState,
    ) -> ToolSelection:

        tools = []
        reasons = []

        requirements = state.metadata.get(
            "task_requirements",
            {},
        )

        if not isinstance(requirements, dict):
            requirements = {}

        # ======================================================
        # DOCUMENTS
        # ======================================================

        if requirements.get("document_required"):
            tools.append("documents")
            reasons.append(
                "The task requires processing a local document."
            )
        elif (
            state.metadata.get("file_path")
            or state.metadata.get("document_path")
        ):
            tools.append("documents")
            reasons.append(
                "A local document/file is involved."
            )

        # ======================================================
        # VISION
        # ======================================================

        if requirements.get("vision_required"):
            tools.append("vision")
            reasons.append(
                "The task requires visual analysis."
            )
        elif state.has_image:
            tools.append("vision")
            reasons.append(
                "An image was supplied."
            )

                # ======================================================
        # KNOWLEDGE / RAG
        # ======================================================

        rag_required = False

        # Planner requirements are stored as a dictionary.
        if isinstance(state.task_requirements, dict):
            rag_required = bool(
                state.task_requirements.get(
                    "rag_required",
                    False,
                )
            )

        # Backward compatibility with the older
        # TaskRequirements dataclass.
        elif state.task_requirements is not None:
            rag_required = bool(
                getattr(
                    state.task_requirements,
                    "rag_required",
                    False,
                )
            )

        # Also accept planner requirements stored in metadata.
        metadata_requirements = state.metadata.get(
            "task_requirements"
        )

        if isinstance(metadata_requirements, dict):
            rag_required = rag_required or bool(
                metadata_requirements.get(
                    "rag_required",
                    False,
                )
            )

        if rag_required:
            tools.append("knowledge_search")
            reasons.append(
                "The task requires private organizational "
                "knowledge."
            )
        # ======================================================
        # CALCULATOR
        # ======================================================

        if requirements.get("calculator_required"):
            tools.append("calculator")
            reasons.append(
                "The task requires deterministic calculation."
            )

        # ======================================================
        # PYTHON SANDBOX
        # ======================================================

        if requirements.get("code_execution_required"):
            tools.append("python")
            reasons.append("The task requires sandboxed code execution.")

        # ======================================================
        # ARTIFACT
        # ======================================================

        if requirements.get("artifact_required"):
            tools.append("artifact")
            reasons.append(
                "The task requires generation of a workflow artifact."
            )

        # ======================================================
        # REMOVE DUPLICATES
        # ======================================================

        unique_tools = []
        unique_reasons = []

        for tool, reason in zip(
            tools,
            reasons,
        ):
            if tool not in unique_tools:
                unique_tools.append(tool)
                unique_reasons.append(reason)

        return ToolSelection(
            tools=unique_tools,
            reasons=unique_reasons,
        )
    