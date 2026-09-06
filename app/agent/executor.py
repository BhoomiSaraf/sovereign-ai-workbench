from app.agent.state import AgentState
from app.models.manager import ModelManager
from app.router.model_router import ModelRouter
from app.tools.registry import ToolRegistry
from app.tools.vision import VisionTool




class AgentExecutor:
    """
    Executes an AgentPlan.

    Responsibilities:
        - route models
        - execute approved tools
        - execute multimodal vision analysis
        - retrieve private knowledge
        - construct model context
        - generate the final response
        - record execution events
    """

    def __init__(
        self,
        router: ModelRouter,
        model_manager: ModelManager,
        tool_registry: ToolRegistry,
    ):
        self.router = router
        self.model_manager = model_manager
        self.tool_registry = tool_registry

    def execute(
        self,
        state: AgentState,
    ) -> AgentState:

        try:
            # --------------------------------------------------
            # Route
            # --------------------------------------------------

            self._execute_routing(state)

            # --------------------------------------------------
            # Vision
            # --------------------------------------------------

            if self._should_analyze_image(state):
                self._execute_vision(state)

            # --------------------------------------------------
            # Knowledge
            # --------------------------------------------------

            if self._should_search_knowledge(state):
                self._execute_knowledge_search(state)

            # --------------------------------------------------
            # Calculator
            # --------------------------------------------------

            if self._should_calculate(state):
                self._execute_calculator(state)

                # A pure calculation is a terminal tool call.
                # Do not send a verified calculation through
                # the language model again.
                if self._is_calculation_only(state):
                    state.response = str(
                        state.tool_results["calculator"]
                    )

                    state.completed = True

                    state.add_event(
                        "complete",
                        "success",
                        terminal_tool="calculator",
                    )

                    return state

            # --------------------------------------------------
            # Final generation
            # --------------------------------------------------

            self._generate_response(state)

            state.completed = True

            state.add_event(
                "complete",
                "success",
            )

        except Exception as exc:

            state.error = str(exc)
            state.completed = False

            state.add_event(
                "execution",
                "error",
                error=str(exc),
            )

        return state

    # ==========================================================
    # ROUTING
    # ==========================================================

    def _execute_routing(
        self,
        state: AgentState,
    ) -> None:

        state.add_event(
            "route_model",
            "started",
        )

        decision = self.router.route(
            task=state.user_input,
            has_image=state.has_image,
        )

        state.selected_model = decision.model.name

        state.routing_score = decision.score

        state.routing_reason = decision.reason

        state.task_requirements = (
            decision.task_requirements
        )

        state.add_event(
            "route_model",
            "success",
            model=decision.model.name,
            score=decision.score,
            reason=decision.reason,
        )

    # ==========================================================
    # VISION
    # ==========================================================

    def _should_analyze_image(
        self,
        state: AgentState,
    ) -> bool:

        return (
            state.has_image
            and bool(state.image_path)
        )

    def _execute_vision(
        self,
        state: AgentState,
    ) -> None:

        if not self.tool_registry.has_tool(
            "vision"
        ):
            raise RuntimeError(
                "Vision tool is not registered."
            )

        state.add_event(
            "vision_analysis",
            "started",
        )

        prompt = (
            "Analyze this industrial engineering image "
            "carefully. Identify equipment, component "
            "tags, valves, instruments, connections, "
            "flow direction, safety devices, and any "
            "clearly readable operating parameters. "
            "Preserve tag numbers exactly as shown. "
            "If a label is uncertain, explicitly mark "
            "it as uncertain rather than guessing."
        )

        result = self.tool_registry.execute(
            "vision",
            image_path=state.image_path,
            prompt=prompt,
        )

        state.vision_context = result

        state.tool_results[
            "vision"
        ] = result

        state.metadata[
            "vision_model"
        ] = "qwen2.5-vl-3b"

        state.add_event(
            "vision_analysis",
            "success",
            model="qwen2.5-vl-3b",
        )

    # ==========================================================
    # KNOWLEDGE
    # ==========================================================

    def _should_search_knowledge(
        self,
        state: AgentState,
    ) -> bool:

        requirements = state.task_requirements

        return bool(
            requirements
            and requirements.rag_required
        )

    def _execute_knowledge_search(
        self,
        state: AgentState,
    ) -> None:

        if not self.tool_registry.has_tool(
            "knowledge_search"
        ):
            raise RuntimeError(
                "Knowledge search tool is not registered."
            )

        state.add_event(
            "search_knowledge",
            "started",
        )

        results = self.tool_registry.execute(
            "knowledge_search",
            query=state.user_input,
            top_k=5,
        )

        state.knowledge_context = results

        state.tool_results[
            "knowledge_search"
        ] = results

        state.add_event(
            "search_knowledge",
            "success",
            result_count=len(results),
        )

    # ==========================================================
    # CALCULATOR
    # ==========================================================

    def _should_calculate(
        self,
        state: AgentState,
    ) -> bool:

        text = state.user_input.lower()

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
                keyword in text
                for keyword in keywords
            )
            and any(
                operator in state.user_input
                for operator in operators
            )
        )

    def _is_calculation_only(
        self,
        state: AgentState,
    ) -> bool:

        text = state.user_input.lower().strip()

        calculation_prefixes = [
            "calculate",
            "compute",
            "what is",
            "how much is",
        ]

        return any(
            text.startswith(prefix)
            for prefix in calculation_prefixes
        )

    def _execute_calculator(
        self,
        state: AgentState,
    ) -> None:

        if not self.tool_registry.has_tool(
            "calculator"
        ):
            raise RuntimeError(
                "Calculator tool is not registered."
            )

        state.add_event(
            "calculator",
            "started",
        )

        expression = self._extract_expression(
            state.user_input
        )

        result = self.tool_registry.execute(
            "calculator",
            expression=expression,
        )

        state.tool_results[
            "calculator"
        ] = result

        # Expose tool execution information to the UI,
        # audit layer, and execution trace.
        state.metadata[
            "tool_used"
        ] = "calculator"

        state.metadata[
            "tool_result"
        ] = result

        state.metadata[
            "tool_expression"
        ] = expression

        state.add_event(
            "calculator",
            "success",
            expression=expression,
            result=result,
        )

    # ==========================================================
    # GENERATION
    # ==========================================================

    def _generate_response(
        self,
        state: AgentState,
    ) -> None:

        if not state.selected_model:
            raise RuntimeError(
                "No model selected."
            )

        # Use the model selected during the routing step.
        # Do not route the same task again.
        model = next(
            (
                model
                for model in self.router.models
                if model.name == state.selected_model
            ),
            None,
        )

        if model is None:
            raise RuntimeError(
                f"Selected model '{state.selected_model}' "
                "is not available."
            )

        prompt = self._build_prompt(state)

        state.add_event(
            "generate_response",
            "started",
            model=model.name,
        )

        response = self.model_manager.generate(
            model=model,
            prompt=prompt,
        )

        state.response = response

        state.add_event(
            "generate_response",
            "success",
            model=model.name,
        )

    # ==========================================================
    # PROMPT CONSTRUCTION
    # ==========================================================

    def _build_prompt(
        self,
        state: AgentState,
    ) -> str:

        sections = [
            "You are the local AI assistant "
            "inside a sovereign, air-gapped "
            "enterprise AI workbench.",
            "",
            "User request:",
            state.user_input,
        ]

        # --------------------------------------------------
        # Vision context
        # --------------------------------------------------

        if state.vision_context:

            sections.extend(
                [
                    "",
                    "VISUAL ANALYSIS:",
                    state.vision_context,
                    "",
                    "Use the visual analysis as evidence. "
                    "Do not invent component tags or values. "
                    "If the visual analysis marks something "
                    "uncertain, preserve that uncertainty.",
                ]
            )

        # --------------------------------------------------
        # Private knowledge
        # --------------------------------------------------

        if state.knowledge_context:

            sections.extend(
                [
                    "",
                    "PRIVATE ORGANIZATIONAL "
                    "KNOWLEDGE:",
                ]
            )

            for index, item in enumerate(
                state.knowledge_context,
                start=1,
            ):
                sections.extend(
                    [
                        "",
                        f"[Source {index}: "
                        f"{item.get('source', 'unknown')}]",
                        item.get(
                            "text",
                            "",
                        ),
                    ]
                )

            sections.extend(
                [
                    "",
                    "Use the private knowledge "
                    "when answering. Do not invent "
                    "organizational policies or facts "
                    "not supported by the retrieved "
                    "material.",
                ]
            )

        # --------------------------------------------------
        # Calculator result
        # --------------------------------------------------

        if state.tool_results.get(
            "calculator"
        ) is not None:

            sections.extend(
                [
                    "",
                    "CALCULATOR RESULT:",
                    str(
                        state.tool_results[
                            "calculator"
                        ]
                    ),
                    "",
                    "Use this verified calculation "
                    "result rather than recalculating "
                    "it yourself.",
                ]
            )

        return "\n".join(
            sections
        )

    # ==========================================================
    # CALCULATOR PARSING
    # ==========================================================

    def _extract_expression(
        self,
        text: str,
    ) -> str:

        expression = text.lower()

        prefixes = [
            "calculate",
            "compute",
            "what is",
            "how much is",
        ]

        for prefix in prefixes:

            if expression.startswith(prefix):

                expression = expression[
                    len(prefix):
                ]

                break

        return (
            expression
            .replace("?", "")
            .strip()
        )