from dataclasses import dataclass
from typing import Dict, List

from app.router.model_registry import (
    ModelConfig,
    get_available_models,
)


@dataclass
class TaskRequirements:
    """
    Describes what a task requires.

    This describes the TASK, not the model.

    Example:

        capabilities={
            "coding": 5,
            "debugging": 5,
        }

        modalities=["text"]
    """

    capabilities: Dict[str, int]
    modalities: List[str]

    # Reserved for future hardware-aware routing.
    complexity: str = "medium"

    # RAG is a workflow requirement, not a model capability.
    rag_required: bool = False

    @property
    def primary_capability(self) -> str:
        """
        Return the most important capability for the task.
        """

        if not self.capabilities:
            return "general"

        return max(
            self.capabilities,
            key=self.capabilities.get,
        )


@dataclass
class RoutingDecision:
    """
    Complete result of the model-routing process.

    This object is useful for both:
        1. The agent
        2. The UI routing panel
    """

    model: ModelConfig
    score: float
    task_requirements: TaskRequirements
    matched_capabilities: List[str]
    reason: List[str]


class ModelRouter:
    """
    Selects the most appropriate local model.

    Routing process:

        User task
            ↓
        Task analysis
            ↓
        Required capabilities
            ↓
        Modality filtering
            ↓
        Capability scoring
            ↓
        Priority tie-breaker
            ↓
        RoutingDecision

    This router is deliberately deterministic for the MVP.
    """

    def __init__(self):
        self.models = get_available_models()

    # ================================================================
    # PUBLIC API
    # ================================================================

    def route(
        self,
        task: str,
        has_image: bool = False,
    ) -> RoutingDecision:
        """
        Analyze a task and select the best registered model.
        """

        requirements = self._analyze_task(
            task=task,
            has_image=has_image,
        )

        candidates = []

        for model in self.models:

            # --------------------------------------------------------
            # HARD FILTER
            # --------------------------------------------------------
            #
            # If the task requires an image but the model cannot
            # accept images, eliminate that model immediately.
            #
            if not self._supports_modalities(
                model=model,
                required_modalities=requirements.modalities,
            ):
                continue

            # --------------------------------------------------------
            # CAPABILITY SCORE
            # --------------------------------------------------------

            score = self._calculate_score(
                model=model,
                requirements=requirements,
            )

            candidates.append(
                (model, score)
            )

        if not candidates:
            raise ValueError(
                "No registered model supports the required "
                f"modalities: {requirements.modalities}"
            )

        # ------------------------------------------------------------
        # SELECT BEST MODEL
        # ------------------------------------------------------------
        #
        # First priority:
        #     capability score
        #
        # Second priority:
        #     lower priority number
        #
        candidates.sort(
            key=lambda item: (
                item[1],
                -item[0].priority,
            ),
            reverse=True,
        )

        selected_model, selected_score = candidates[0]

        matched_capabilities = [
            capability
            for capability in requirements.capabilities
            if capability in selected_model.capabilities
        ]

        reason = self._build_reason(
            selected_model=selected_model,
            requirements=requirements,
            matched_capabilities=matched_capabilities,
        )

        return RoutingDecision(
            model=selected_model,
            score=selected_score,
            task_requirements=requirements,
            matched_capabilities=matched_capabilities,
            reason=reason,
        )

    def route_model(
        self,
        task: str,
        has_image: bool = False,
    ) -> ModelConfig:
        """
        Convenience method.

        Returns only the selected ModelConfig.

        Useful when existing code does not need the
        complete RoutingDecision.
        """

        decision = self.route(
            task=task,
            has_image=has_image,
        )

        return decision.model

    # ================================================================
    # TASK ANALYSIS
    # ================================================================

    def _analyze_task(
        self,
        task: str,
        has_image: bool,
    ) -> TaskRequirements:
        """
        Convert natural-language input into task requirements.

        This is intentionally deterministic for the MVP.

        Later we can improve this with:
            - semantic classification
            - hardware awareness
            - context-length requirements
            - model availability
        """

        task_lower = task.lower()

        capabilities: Dict[str, int] = {}

        # Every normal request starts with text.
        modalities = ["text"]

        # ============================================================
        # VISION
        # ============================================================

        vision_keywords = [
            "image",
            "photo",
            "scanned",
            "scan",
            "p&id",
            "pid",
            "drawing",
            "diagram",
            "visual",
            "picture",
            "photograph",
        ]

        if has_image or any(
            keyword in task_lower
            for keyword in vision_keywords
        ):
            capabilities["vision"] = 5
            capabilities["image_analysis"] = 5

            if "image" not in modalities:
                modalities.append("image")

        # ============================================================
        # CODING
        # ============================================================

        coding_keywords = [
            "code",
            "coding",
            "python",
            "program",
            "programming",
            "debug",
            "debugging",
            "script",
            "function",
            "bug",
            "software",
            "source code",
            "algorithm",
            "class",
            "api",
        ]

        if any(
            keyword in task_lower
            for keyword in coding_keywords
        ):
            capabilities["coding"] = 5
            capabilities["programming"] = 5

        # ============================================================
        # DEBUGGING
        # ============================================================

        debugging_keywords = [
            "debug",
            "debugging",
            "bug",
            "error",
            "fix this code",
            "fix the code",
            "not working",
        ]

        if any(
            keyword in task_lower
            for keyword in debugging_keywords
        ):
            capabilities["debugging"] = 5

        # ============================================================
        # CODE REVIEW
        # ============================================================

        review_keywords = [
            "code review",
            "review this code",
            "review the code",
            "review my code",
        ]

        if any(
            keyword in task_lower
            for keyword in review_keywords
        ):
            capabilities["code_review"] = 5

        # ============================================================
        # REASONING
        # ============================================================

        reasoning_keywords = [
            "analyze",
            "analyse",
            "compare",
            "explain",
            "evaluate",
            "assess",
            "reason",
            "recommend",
            "determine",
            "identify",
        ]

        if any(
            keyword in task_lower
            for keyword in reasoning_keywords
        ):
            capabilities["reasoning"] = 4

        # ============================================================
        # DOCUMENT ANALYSIS
        # ============================================================

        document_keywords = [
            "document",
            "report",
            "inspection report",
            "manual",
            "sop",
            "policy",
            "pdf",
            "approval note",
            "technical document",
        ]

        if any(
            keyword in task_lower
            for keyword in document_keywords
        ):
            capabilities["document_analysis"] = 4

        # ============================================================
        # SUMMARIZATION
        # ============================================================

        summarization_keywords = [
            "summarize",
            "summarise",
            "summary",
            "give me a summary",
            "brief",
            "condense",
        ]

        if any(
            keyword in task_lower
            for keyword in summarization_keywords
        ):
            capabilities["summarization"] = 5

        # ============================================================
        # RAG
        # ============================================================

        rag_keywords = [
            "according to our",
            "according to the sop",
            "according to our sop",
            "according to the manual",
            "our policy",
            "company policy",
            "internal policy",
            "internal document",
            "organizational",
            "organization's",
            "knowledge base",
            "knowledgebase",
            "internal knowledge",
        ]

        rag_required = any(
            keyword in task_lower
            for keyword in rag_keywords
        )

        # ============================================================
        # DEFAULT
        # ============================================================

        if not capabilities:
            capabilities["general"] = 4
            capabilities["reasoning"] = 3

        # ============================================================
        # COMPLEXITY
        # ============================================================

        complexity = self._estimate_complexity(
            task_lower=task_lower,
            capabilities=capabilities,
        )

        return TaskRequirements(
            capabilities=capabilities,
            modalities=modalities,
            complexity=complexity,
            rag_required=rag_required,
        )

    # ================================================================
    # SCORING
    # ================================================================

    def _calculate_score(
        self,
        model: ModelConfig,
        requirements: TaskRequirements,
    ) -> float:
        """
        Calculate model/task compatibility.

        For every required capability:

            model capability strength
            ×
            task requirement strength

        is added to the total.

        Priority is deliberately only a tiny tie-breaker.
        """

        score = 0.0

        for (
            capability,
            requirement_strength,
        ) in requirements.capabilities.items():

            model_strength = model.capabilities.get(
                capability,
                0,
            )

            score += (
                model_strength
                * requirement_strength
            )

        return score

    # ================================================================
    # MODALITY CHECK
    # ================================================================

    def _supports_modalities(
        self,
        model: ModelConfig,
        required_modalities: List[str],
    ) -> bool:
        """
        Return True only if the model supports every
        required input modality.
        """

        return all(
            modality in model.modalities
            for modality in required_modalities
        )

    # ================================================================
    # COMPLEXITY
    # ================================================================

    def _estimate_complexity(
        self,
        task_lower: str,
        capabilities: Dict[str, int],
    ) -> str:
        """
        Lightweight deterministic complexity estimate.

        This is deliberately simple for the MVP.
        """

        complexity_signals = 0

        instruction_words = [
            "and",
            "then",
            "compare",
            "verify",
            "generate",
            "create",
            "validate",
        ]

        complexity_signals += sum(
            task_lower.count(word)
            for word in instruction_words
        )

        if len(capabilities) >= 3:
            complexity_signals += 2

        if len(capabilities) >= 5:
            complexity_signals += 2

        if complexity_signals >= 6:
            return "high"

        if complexity_signals >= 3:
            return "medium"

        return "low"

    # ================================================================
    # EXPLANATION
    # ================================================================

    def _build_reason(
        self,
        selected_model: ModelConfig,
        requirements: TaskRequirements,
        matched_capabilities: List[str],
    ) -> List[str]:
        """
        Generate human-readable routing explanations.

        These will later be displayed in the UI.
        """

        reasons = []

        if matched_capabilities:
            reasons.append(
                "Matched capabilities: "
                + ", ".join(matched_capabilities)
            )

        if "image" in requirements.modalities:
            reasons.append(
                "Image input requires a multimodal model."
            )

        if requirements.rag_required:
            reasons.append(
                "Task requires organizational knowledge; "
                "RAG should be invoked separately."
            )

        reasons.append(
            f"Task complexity: {requirements.complexity}."
        )

        reasons.append(
            f"Selected model: {selected_model.name}."
        )

        return reasons