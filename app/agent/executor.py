from app.agent.state import AgentState
from app.agent.tool_selector import ToolSelector
from app.models.manager import ModelManager
from app.multimodal.page_selector import SemanticPageSelector
from app.router.model_registry import get_model_by_name
from app.router.model_router import ModelRouter
from app.tools.registry import ToolRegistry


class AgentExecutor:

    def __init__(
        self,
        router: ModelRouter,
        model_manager: ModelManager,
        tool_registry: ToolRegistry,
    ):
        self.router = router
        self.model_manager = model_manager
        self.tool_registry = tool_registry
        self.tool_selector = ToolSelector()

        # Local semantic relevance selector.
        #
        # It uses the local embedding model and does not contain
        # task-specific keywords.
        self.page_selector = SemanticPageSelector()

    # ==========================================================
    # MAIN EXECUTION
    # ==========================================================

    def execute(
        self,
        state: AgentState,
    ) -> AgentState:

        try:

            plan = list(
                state.metadata.get(
                    "plan",
                    [],
                )
            )

            if not plan:
                plan = [
                    "analyze_task",
                    "route_model",
                    "generate_response",
                ]

            # Keep the planner's original plan unchanged.
            state.metadata["plan"] = list(plan)

            # Validation is an execution-stage requirement,
            # not part of the planner's original plan.
            execution_plan = list(plan)

            if "validate" not in execution_plan:
                execution_plan.append("validate")
            state.metadata["execution_mode"] = (
                "iterative_plan_driven"
            )

            state.status = "planning"

            state.add_event(
                "plan",
                "start",
                steps=list(plan),
            )

            remaining = list(execution_plan)

            while remaining:

                if not state.begin_iteration():
                    state.status = "failed"
                    state.error = (
                        "Maximum agent iterations exceeded."
                    )

                    state.add_event(
                        "execution",
                        "error",
                        error=state.error,
                    )

                    return state

                step = remaining[0]

                state.current_step = step
                state.status = "acting"

                state.add_event(
                    "step",
                    "start",
                    step=step,
                    iteration=state.iteration,
                )

                if step in state.completed_steps:

                    remaining.pop(0)

                    state.add_event(
                        "step",
                        "skipped",
                        step=step,
                        reason="Already completed.",
                    )

                    continue

                try:

                    self._dispatch_step(
                        state,
                        step,
                    )

                except Exception as exc:

                    state.mark_step_failed(step)

                    state.observe(
                        step,
                        False,
                        error=str(exc),
                    )

                    state.add_event(
                        "decision",
                        "failure",
                        step=step,
                        error=str(exc),
                    )

                    if self._decide_recovery(
                        state,
                        step,
                        str(exc),
                    ):

                        state.add_event(
                            "replan",
                            "recovery",
                            failed_step=step,
                            remaining_steps=list(
                                remaining
                            ),
                        )

                        continue

                    raise

                # --------------------------------------------------
                # OBSERVE
                # --------------------------------------------------

                success = self._step_succeeded(
                    state,
                    step,
                )

                state.observe(
                    step,
                    success,
                )

                # --------------------------------------------------
                # DECIDE
                # --------------------------------------------------

                if not success:

                    state.mark_step_failed(step)

                    if self._decide_recovery(
                        state,
                        step,
                        self._step_error(
                            state,
                            step,
                        ),
                    ):
                        continue

                    raise RuntimeError(
                        self._step_error(
                            state,
                            step,
                        )
                    )

                state.mark_step_complete(step)

                self._complete_step(
                    state,
                    step,
                )

                state.decision = "continue"
                # A calculation-only request already has its final answer.
                # Skip unnecessary LLM response generation, but still run
                # the mandatory validation stage.
                if (
                    step == "calculator"
                    and self._is_calculation_only(state)
                ):
                    remaining = ["validate"]
                else:
                    remaining = [
                        item
                        for item in remaining[1:]
                        if item
                        not in state.completed_steps
                    ]
                

                state.metadata[
                    "remaining_plan"
                ] = list(remaining)

                state.add_event(
                    "decision",
                    "continue",
                    completed_step=step,
                    remaining_steps=list(
                        remaining
                    ),
                )

                state.add_event(
                    "replan",
                    "complete",
                    remaining_steps=list(
                        remaining
                    ),
                )

            # ------------------------------------------------------
            # FINISH
            # ------------------------------------------------------

            state.current_step = None
            state.status = "completed"
            state.completed = True

            state.add_event(
                "plan",
                "complete",
                completed_steps=list(
                    state.completed_steps
                ),
            )

            state.add_event(
                "execution",
                "complete",
                iterations=state.iteration,
            )

            return state

        except Exception as exc:

            state.current_step = None
            state.status = "failed"
            state.error = str(exc)
            state.completed = False

            state.add_event(
                "execution",
                "error",
                error=str(exc),
                iteration=state.iteration,
            )

            return state

    def _dispatch_step(
        self,
        state: AgentState,
        step: str,
    ) -> None:

        if step == "analyze_task":

            state.add_event(
                "observation",
                "complete",
                step=step,
                requirements=state.task_requirements,
            )

        elif step == "route_model":

            self._execute_routing(state)
            self._select_tools(state)

        elif step == "process_document":

            if self._should_process_document(state):
                self._execute_document_processing(state)
            else:
                state.add_event(
                    "step",
                    "skipped",
                    step=step,
                    reason="Document processing not required.",
                )

        elif step == "analyze_image":

            if self._should_analyze_image(state):
                self._execute_vision(state)
            else:
                state.add_event(
                    "step",
                    "skipped",
                    step=step,
                    reason="Vision analysis not required.",
                )

        elif step == "search_knowledge":

            if self._should_search_knowledge(state):
                self._execute_knowledge_search(state)
            else:
                state.add_event(
                    "step",
                    "skipped",
                    step=step,
                    reason="Knowledge search not required.",
                )

        elif step == "calculator":

            if self._should_calculate(state):

                self._execute_calculator(state)

                if self._is_calculation_only(state):

                    result = state.tool_results[
                        "calculator"
                    ]

                    if hasattr(result, "result"):
                        state.response = str(
                            result.result
                        )
                    else:
                        state.response = str(result)

                    state.metadata[
                        "tool_result"
                    ] = (
                        result.result
                        if hasattr(result, "result")
                        else result
                    )

                    state.evidence.setdefault(
                        "inference",
                        [],
                    ).append(
                        {
                            "conclusion": state.response,
                            "supporting_evidence": {},
                        }
                    )

            else:
                state.add_event(
                    "step",
                    "skipped",
                    step=step,
                    reason="Calculation not required.",
                )

        elif step == "code_execution":

            if self._should_execute_code(state):
                self._execute_code(state)
            else:
                state.add_event(
                    "step",
                    "skipped",
                    step=step,
                    reason="Code execution not required.",
                )

        elif step == "generate_response":

            self._generate_response(state)

        elif step == "generate_artifact":

            if self._should_generate_artifact(state):
                self._execute_artifact(state)
            else:
                state.add_event(
                    "step",
                    "skipped",
                    step=step,
                    reason="Artifact generation not required.",
                )

        elif step == "validate":

            self._validate_final_state(state)

        else:

            raise ValueError(
                f"Unknown agent plan step: {step}"
            )

    def _step_succeeded(
        self,
        state: AgentState,
        step: str,
    ) -> bool:

        if step == "code_execution":

            result = state.tool_results.get(
                "code_execution"
            )

            if result is None:
                return False

            if hasattr(result, "get"):
                return bool(
                    result.get(
                        "success",
                        False,
                    )
                )

            return bool(result)

        if step == "validate":
            return bool(
                state.validation.get(
                    "valid",
                    False,
                )
            )

        return True

    def _step_error(
        self,
        state: AgentState,
        step: str,
    ) -> str:

        result = state.tool_results.get(
            step
        )

        if hasattr(result, "get"):

            return str(
                result.get(
                    "error"
                )
                or result.get(
                    "stderr"
                )
                or "Tool execution failed."
            )

        return (
            state.error
            or f"{step} failed."
        )

    def _decide_recovery(
        self,
        state: AgentState,
        step: str,
        error: str,
    ) -> bool:

        # Code execution gets an explicit repair loop.
        # Python is the first supported runtime.
        if step == "code_execution":

            if state.can_retry(
                "code_repair",
                limit=2,
            ):

                state.mark_step_failed(
                    "code_repair"
                )

                self._repair_python(
                    state,
                    error,
                )

                return True

        # Artifact generation can be retried once.
        if step == "generate_artifact":

            if state.can_retry(
                "artifact",
                limit=1,
            ):

                state.mark_step_failed(
                    "artifact"
                )

                state.completed_steps = [
                    item
                    for item in state.completed_steps
                    if item != "generate_artifact"
                ]

                return True

        # Response generation can be retried once.
        if step == "generate_response":

            if state.can_retry(
                "response",
                limit=1,
            ):

                state.mark_step_failed(
                    "response"
                )

                return True

        return False

    # ==========================================================
    # ITERATIVE PYTHON EXECUTION
    # ==========================================================

    def _execute_python_iterative(
        self,
        state: AgentState,
    ) -> None:

        code = state.metadata.get(
            "code"
        )

        if not code:

            code = self._generate_python_code(
                state
            )

            state.metadata[
                "code"
            ] = code

            state.add_event(
                "code_generation",
                "complete",
            )

        task_id = state.metadata.get(
            "task_id"
        )

        workspace_root = state.metadata.get(
            "workspace_root"
        )

        result = self.tool_registry.execute(
            "python",
            code=code,
            task_id=task_id,
            workspace_root=workspace_root,
        )

        state.tool_results[
            "python"
        ] = result

        # Generic execution result used by the planner/executor
        # state machine. Keep the Python key for compatibility
        # with existing tests and prompt construction.
        state.tool_results[
            "code_execution"
        ] = result

        if hasattr(result, "get"):
            success = result.get(
                "success",
                False,
            )
            error = result.get(
                "error"
            ) or result.get(
                "stderr"
            )
        else:
            success = bool(result)
            error = None

        state.add_event(
            "tool",
            "complete" if success else "failed",
            tool="code_execution",
            runtime="python",
            success=success,
            error=error,
        )

    def _generate_python_code(
        self,
        state: AgentState,
    ) -> str:

        model = get_model_by_name(
            state.selected_model
        )

        prompt = f"""
You are the local coding agent inside a sovereign,
air-gapped AI workbench.

Generate Python code that solves the user's task.

USER REQUEST:
{state.user_input}

RULES:
- Return ONLY executable Python code.
- Do not use markdown fences.
- Do not access the network.
- Do not access files outside /workspace.
- Use standard Python libraries unless the task explicitly
  requires something already available locally.
- Print the important final result.
- Keep the program deterministic.

The program will be executed inside a restricted sandbox.
"""

        code = self.model_manager.generate(
            model=model,
            prompt=prompt,
        )

        return self._clean_generated_code(
            code
        )

    def _repair_python(
        self,
        state: AgentState,
        error: str,
    ) -> None:

        old_code = state.metadata.get(
            "code",
            "",
        )

        model = get_model_by_name(
            state.selected_model
        )

        prompt = f"""
You are repairing Python code inside a sovereign,
air-gapped AI workbench.

USER REQUEST:
{state.user_input}

CURRENT CODE:
{old_code}

EXECUTION ERROR:
{error}

TASK:
Return corrected Python code that solves the original
request and fixes the execution error.

RULES:
- Return ONLY executable Python code.
- Do not use markdown fences.
- Do not use network access.
- Do not access files outside /workspace.
- Preserve correct parts of the existing solution.
- Make the smallest reliable correction.
- Print the important final result.
"""

        repaired = self.model_manager.generate(
            model=model,
            prompt=prompt,
        )

        state.metadata[
            "code"
        ] = self._clean_generated_code(
            repaired
        )

        state.add_event(
            "decision",
            "repair",
            reason="Code execution failed.",
            runtime="python",
            repair_attempt=state.retry_counts.get(
                "code_repair",
                0,
            ),
        )

        # Remove the failed generic code-execution step so it
        # is executed again on the next iteration.
        state.completed_steps = [
            item
            for item in state.completed_steps
            if item != "code_execution"
        ]

    @staticmethod
    def _clean_generated_code(
        code: str,
    ) -> str:

        text = str(code).strip()

        if text.startswith(
            "```python"
        ):
            text = text[
                len("```python"):
            ]

        elif text.startswith(
            "```"
        ):
            text = text[
                len("```"):
            ]

        if text.endswith(
            "```"
        ):
            text = text[:-3]

        return text.strip()

    # ==========================================================
    # FINAL VALIDATION
    # ==========================================================

    def _validate_final_state(
        self,
        state: AgentState,
    ) -> None:

        from app.agent.validator import (
            AgentValidator,
        )

        validator = AgentValidator()

        validation = validator.validate(
            state
        )

        state.validation = validation

        state.add_event(
            "validation",
            "complete" if validation[
                "valid"
            ] else "failed",
            validation=validation,
        )

        if not validation["valid"]:

            # A Python failure should be handled by the
            # iterative recovery loop.
            code_result = validation.get(
                "code",
                {},
            )

            if not code_result.get(
                "success",
                True,
            ):

                raise RuntimeError(
                    code_result.get(
                        "message",
                        "Code validation failed.",
                    )
                )

            raise RuntimeError(
                "Final validation failed."
            )    # ==========================================================
    # AGENT EXECUTION PROGRESS
    # ==========================================================

    def _complete_step(
        self,
        state: AgentState,
        step: str,
    ) -> None:
        """
        Record a successfully handled plan step once.
        """

        if step not in state.completed_steps:

            state.completed_steps.append(
                step
            )

        state.add_event(
            "step",
            "complete",
            step=step,
        )

    def _replan_remaining(
        self,
        state: AgentState,
    ) -> None:
        """
        Refresh the remaining plan after each observation.

        The original plan is kept unchanged for compatibility.
        The current remaining work is exposed separately through
        state.metadata["remaining_plan"].
        """

        original_plan = state.metadata.get(
            "plan",
            [],
        )

        remaining = [
            step
            for step in original_plan
            if step not in state.completed_steps
        ]

        state.metadata[
            "remaining_plan"
        ] = remaining

        state.add_event(
            "replan",
            "complete",
            remaining_steps=list(
                remaining
            ),
        )

    # ==========================================================
    # ROUTING
    # ==========================================================

    def _execute_routing(
        self,
        state: AgentState,
    ):
        decision = self.router.route(
            state.user_input,
            has_image=state.has_image,
        )

        state.selected_model = decision.model.name
        state.routing_score = decision.score
        state.routing_reason = decision.reason

        # The planner owns execution requirements.
        #
        # Router requirements are useful for model-routing
        # information, but must not overwrite planner decisions
        # such as RAG, vision, document, or artifact requirements.
        state.metadata["routing_task_requirements"] = (
            decision.task_requirements
        )

        state.add_event(
            "routing",
            "complete",
            model=decision.model.name,
            score=decision.score,
            reason=decision.reason,
        )

    # ==========================================================
    # TOOL SELECTION
    # ==========================================================

    def _select_tools(
        self,
        state: AgentState,
    ):

        selection = self.tool_selector.select(
            state
        )

        state.metadata["selected_tools"] = (
            selection.tools
        )

        state.metadata[
            "tool_selection_reasons"
        ] = selection.reasons

        state.add_event(
            "tool_selection",
            "complete",
            tools=selection.tools,
            reasons=selection.reasons,
        )

    def _has_selected_tool(
        self,
        state: AgentState,
        tool_name: str,
    ) -> bool:

        return tool_name in state.metadata.get(
            "selected_tools",
            [],
        )

    # ==========================================================
    # DOCUMENTS
    # ==========================================================

    def _should_process_document(
        self,
        state: AgentState,
    ) -> bool:

        return (
            self._has_selected_tool(
                state,
                "documents",
            )
            and bool(
                state.metadata.get(
                    "file_path"
                )
                or state.metadata.get(
                    "document_path"
                )
            )
        )

    def _execute_document_processing(
        self,
        state: AgentState,
    ):

        if not self.tool_registry.has_tool(
            "documents"
        ):
            raise RuntimeError(
                "Document tool is not registered."
            )

        file_path = (
            state.metadata.get(
                "file_path"
            )
            or state.metadata.get(
                "document_path"
            )
        )

        result = self.tool_registry.execute(
            "documents",
            file_path=file_path,
        )

        state.tool_results["documents"] = result
        state.metadata["document_result"] = result

        # Structured evidence.
        state.evidence.setdefault(
            "document",
            [],
        ).append(
            {
                "claim": (
                    "Document was successfully "
                    "processed by the local "
                    "document pipeline."
                ),
                "source": result.get(
                    "source"
                ),
                "page_count": result.get(
                    "page_count"
                ),
                "ocr_used": result.get(
                    "ocr_used"
                ),
                "confidence": 1.0,
            }
        )

        state.add_event(
            "tool",
            "complete",
            tool="documents",
            ocr_used=result.get(
                "ocr_used"
            ),
            page_count=result.get(
                "page_count"
            ),
            rendered_pages=len(
                result.get(
                    "rendered_pages",
                    [],
                )
            ),
        )

    # ==========================================================
    # VISION
    # ==========================================================

    def _should_analyze_image(
        self,
        state: AgentState,
    ) -> bool:

        if not self._has_selected_tool(
            state,
            "vision",
        ):
            return False

        # Direct image input.
        if (
            state.has_image
            and state.image_path
        ):
            return True

        # Scanned PDF with rendered pages.
        document_result = (
            state.tool_results.get(
                "documents"
            )
        )

        if isinstance(
            document_result,
            dict,
        ):

            return bool(
                document_result.get(
                    "ocr_used",
                    False,
                )
                and document_result.get(
                    "rendered_pages",
                    [],
                )
            )

        return False

    def _select_vision_pages(
        self,
        state: AgentState,
        top_k: int = 1,
    ):
        """
        Select relevant rendered document pages using local
        semantic similarity.

        No document-specific keywords are used.
        """

        document_result = (
            state.tool_results.get(
                "documents"
            )
        )

        if not isinstance(
            document_result,
            dict,
        ):
            return []

        rendered_pages = (
            document_result.get(
                "rendered_pages",
                [],
            )
        )

        page_texts = (
            document_result.get(
                "page_texts",
                [],
            )
        )

        if not rendered_pages:
            return []

        # Fail loudly instead of silently pairing the wrong
        # OCR text with the wrong image.
        if len(rendered_pages) != len(
            page_texts
        ):
            raise ValueError(
                "Rendered pages and OCR page texts "
                "are misaligned."
            )

        return self.page_selector.select(
            query=state.user_input,
            pages=rendered_pages,
            page_texts=page_texts,
            top_k=top_k,
        )

    def _execute_vision(
        self,
        state: AgentState,
    ):

        if not self.tool_registry.has_tool(
            "vision"
        ):
            raise RuntimeError(
                "Vision tool is not registered."
            )

        # ------------------------------------------------------
        # Determine image(s)
        # ------------------------------------------------------

        pages = []

        # Direct image input.
        if (
            state.has_image
            and state.image_path
        ):

            pages = [
                {
                    "page_number": None,
                    "image_path": state.image_path,
                    "relevance_score": 1.0,
                }
            ]

        # Document-derived images.
        else:

            selected = self._select_vision_pages(
                state,
                top_k=1,
            )

            pages = [
                {
                    "page_number": page.page_number,
                    "image_path": page.image_path,
                    "relevance_score": page.score,
                }
                for page in selected
            ]

        if not pages:
            state.add_event(
                "tool",
                "skipped",
                tool="vision",
                reason=(
                    "No usable image was available."
                ),
            )
            return

        # ------------------------------------------------------
        # Analyze selected image(s)
        # ------------------------------------------------------

        outputs = []

        for page in pages:

            image_path = page[
                "image_path"
            ]

            prompt = f"""
        Analyze the supplied image in relation to the user's request.

        USER REQUEST:
        {state.user_input}

        Treat the image as visual evidence only.

        Return only observations that are directly supported by
        the image.

        Separate your response into:

        1. Directly visible information.
        2. Uncertain or ambiguous observations.

        Do NOT invent:
        - labels
        - values
        - measurements
        - equipment states
        - relationships
        - operating conditions

        Do NOT infer or claim:
        - operational status
        - safe or unsafe operation
        - fitness for service
        - compliance
        - remaining life
        - structural integrity
        - active leakage
        - failure
        - maintenance completion

        unless the supplied image explicitly provides evidence for
        that claim.

        If operational status is not directly established by the
        image, state:

        "Operational status cannot be determined from the image."

        If leakage is not directly visible and unambiguous, describe
        it as staining, discoloration, moisture, or a possible leakage
        indicator rather than claiming that an active leak exists.

        If a measurement is not clearly readable directly from the
        image, do not invent or estimate it.

        If text or a tag is difficult to read, explicitly mark it
        as uncertain.

        Do not treat information that is merely implied by the
        equipment type, diagram, context, or domain knowledge as
        direct visual evidence.

        The image is not proof of actual physical operating
        condition unless that condition is directly observable.

        Return only observations supported by the image.
        """


            result = self.tool_registry.execute(
                "vision",
                image_path=image_path,
                prompt=prompt,
            )

            outputs.append(
                {
                    "page_number": page[
                        "page_number"
                    ],
                    "image_path": image_path,
                    "relevance_score": page[
                        "relevance_score"
                    ],
                    "analysis": result,
                }
            )

        # ------------------------------------------------------
        # Preserve existing state fields
        # ------------------------------------------------------

        state.vision_context = "\n\n".join(
            str(item["analysis"])
            for item in outputs
        )

        state.tool_results["vision"] = outputs

        # Preserve current metadata behavior.
        state.metadata["vision_pages"] = [
            {
                "page_number": item[
                    "page_number"
                ],
                "image_path": item[
                    "image_path"
                ],
                "relevance_score": item[
                    "relevance_score"
                ],
            }
            for item in outputs
        ]

        # Existing vision model metadata.
        #
        # This is metadata describing the current registered
        # vision implementation, not a routing decision.
        state.metadata["vision_model"] = (
            "qwen2.5-vl-3b"
        )

        # ------------------------------------------------------
        # Structured evidence
        # ------------------------------------------------------

        for item in outputs:

            state.evidence.setdefault(
                "vision",
                [],
            ).append(
                {
                    "observation": item[
                        "analysis"
                    ],
                    "source": item[
                        "image_path"
                    ],
                    "page": item[
                        "page_number"
                    ],
                    "relevance": item[
                        "relevance_score"
                    ],
                }
            )

        state.add_event(
            "vision_analysis",
            "complete",
            model=state.metadata.get(
                "vision_model"
            ),
            pages=len(outputs),
            image_paths=[
                item["image_path"]
                for item in outputs
            ],
            summary=state.vision_context,
        )

        state.add_event(
            "tool",
            "complete",
            tool="vision",
            model=state.metadata.get(
                "vision_model"
            ),
            pages=len(outputs),
        )

    # ==========================================================
    # RAG
    # ==========================================================

    def _should_search_knowledge(
        self,
        state: AgentState,
    ) -> bool:

        if not self._has_selected_tool(
            state,
            "knowledge_search",
        ):
            return False

        requirements = state.task_requirements

        if isinstance(requirements, dict):
            return bool(
                requirements.get(
                    "rag_required",
                    False,
                )
            )

        return bool(
            getattr(
                requirements,
                "rag_required",
                False,
            )
        )
    def _execute_knowledge_search(
        self,
        state: AgentState,
    ):
        if not self.tool_registry.has_tool(
            "knowledge_search"
        ):
            raise RuntimeError(
                "Knowledge search tool is not registered."
            )

        result = self.tool_registry.execute(
            "knowledge_search",
            query=state.user_input,
            top_k=5,
        )

        # ------------------------------------------------------
        # Keep retrieval context source-consistent when one
        # source clearly dominates the retrieved results.
        #
        # This is generic: it is not tied to HX-204, pumps,
        # or any specific SOP.
        # ------------------------------------------------------

        if result:
            source_counts = {}

            for item in result:
                source = item.get("source")

                if source:
                    source_counts[source] = (
                        source_counts.get(source, 0) + 1
                    )

            if source_counts:
                dominant_source = max(
                    source_counts,
                    key=source_counts.get,
                )

                dominant_count = source_counts[
                    dominant_source
                ]

                if dominant_count >= 3:
                    result = [
                        item
                        for item in result
                        if item.get("source")
                        == dominant_source
                    ]

        state.knowledge_context = result

        state.tool_results[
            "knowledge_search"
        ] = result

        # Structured private-knowledge evidence.
        for item in result:
            state.evidence.setdefault(
                "knowledge",
                [],
            ).append(
                {
                    "statement": item.get(
                        "text"
                    ),
                    "source": item.get(
                        "source"
                    ),
                    "relevance": item.get(
                        "score"
                    ),
                    "metadata": item.get(
                        "metadata",
                        {},
                    ),
                }
            )

        state.add_event(
            "tool",
            "complete",
            tool="knowledge_search",
            results=len(result),
        )
    # ==========================================================
    # CALCULATOR
    # ==========================================================

    def _should_calculate(
        self,
        state: AgentState,
    ) -> bool:

        return self._has_selected_tool(
            state,
            "calculator",
        )

    def _execute_calculator(
        self,
        state: AgentState,
    ):

        if not self.tool_registry.has_tool(
            "calculator"
        ):
            raise RuntimeError(
                "Calculator tool is not registered."
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
            "tool",
            "complete",
            tool="calculator",
            expression=expression,
            result=result,
        )

    def _is_calculation_only(
        self,
        state: AgentState,
    ) -> bool:

        requirements = state.task_requirements

        code_execution_required = (
            requirements.get(
                "code_execution_required",
                False,
            )
            if isinstance(requirements, dict)
            else False
        )

        return (
            self._has_selected_tool(
                state,
                "calculator",
            )
            and not self._has_selected_tool(
                state,
                "vision",
            )
            and not self._has_selected_tool(
                state,
                "knowledge_search",
            )
            and not code_execution_required
            and not self._has_selected_tool(
                state,
                "documents",
            )
        )

    # ==========================================================
    # CODE EXECUTION
    # ==========================================================

    def _should_execute_code(
        self,
        state: AgentState,
    ) -> bool:

        requirements = state.task_requirements

        if not isinstance(requirements, dict):
            return False

        return bool(
            requirements.get(
                "code_execution_required",
                False,
            )
        )

    def _execute_code(
        self,
        state: AgentState,
    ) -> None:

        requirements = state.task_requirements

        if not isinstance(requirements, dict):
            raise RuntimeError(
                "Code execution requirements are unavailable."
            )

        language = (
            requirements.get("code_language")
            or "python"
        ).lower()

        state.metadata["code_language"] = language

        if language == "python":
            self._execute_python_iterative(state)
            return

        raise RuntimeError(
            f"Code execution runtime '{language}' "
            "is not available in the current MVP."
        )

    # ==========================================================
    # PYTHON
    # ==========================================================

    def _should_execute_python(
        self,
        state: AgentState,
    ) -> bool:

        return self._has_selected_tool(
            state,
            "python",
        )

    def _execute_python(
        self,
        state: AgentState,
    ):

        if not self.tool_registry.has_tool(
            "python"
        ):
            raise RuntimeError(
                "Python tool is not registered."
            )

        code = state.metadata.get(
            "code"
        )

        if not code:

            state.add_event(
                "tool",
                "skipped",
                tool="python",
                reason="No code supplied.",
            )

            return

        result = self.tool_registry.execute(
            "python",
            code=code,
        )

        state.tool_results[
            "python"
        ] = result

        state.add_event(
            "tool",
            "complete",
            tool="python",
            success=result.get(
                "success"
            ),
        )

    # ==========================================================
    # ARTIFACTS
    # ==========================================================

    def _should_generate_artifact(
        self,
        state: AgentState,
    ) -> bool:

        return self._has_selected_tool(
            state,
            "artifact",
        )

    def _execute_artifact(
        self,
        state: AgentState,
    ):

        if not self.tool_registry.has_tool(
            "artifact"
        ):
            raise RuntimeError(
                "Artifact tool is not registered."
            )

        source_document = (
            state.metadata.get(
                "file_path"
            )
            or state.metadata.get(
                "document_path"
            )
        )

        source_name = (
            str(source_document)
            if source_document
            else "Local inspection workflow"
        )

        findings = []

        # Prefer structured evidence where available.
        for item in state.evidence.get(
            "vision",
            [],
        ):
            findings.append(
                str(
                    item.get(
                        "observation",
                        "",
                    )
                )
            )

        # Preserve document extraction behavior.
        if "documents" in state.tool_results:

            document_result = (
                state.tool_results[
                    "documents"
                ]
            )

            if isinstance(
                document_result,
                dict,
            ):

                extracted_text = (
                    document_result.get(
                        "text"
                    )
                )

                if extracted_text:

                    findings.append(
                        str(
                            extracted_text
                        )[:5000]
                    )

        recommendations = []

        if state.response:
            recommendations.append(
                state.response
            )

        uncertainties = []

        if state.vision_context:

            uncertainties.append(
                "Visual analysis is model-generated "
                "and requires human verification "
                "before approval."
            )

        if not state.knowledge_context:

            uncertainties.append(
                "No private organizational knowledge "
                "was retrieved for this workflow."
            )

        result = self.tool_registry.execute(
            "artifact",
            artifact_type="docx",
            title="Inspection Approval Note",
            summary=(
                state.response
                or "Inspection workflow completed."
            ),
            findings=findings,
            recommendations=recommendations,
            knowledge_context=(
                state.knowledge_context
            ),
            uncertainties=uncertainties,
            source_document=source_name,
            filename=(
                "inspection_approval_note.docx"
            ),
        )

        state.tool_results[
            "artifact"
        ] = result

        state.metadata[
            "artifact_path"
        ] = result.get(
            "path"
        )

        state.metadata[
            "artifact_type"
        ] = result.get(
            "artifact_type"
        )

        state.metadata[
            "artifact_validation"
        ] = result.get(
            "validation"
        )

        state.add_event(
            "artifact_generation",
            "complete",
            artifact_type="docx",
            path=result.get(
                "path"
            ),
            validation=result.get(
                "validation"
            ),
        )

    # ==========================================================
    # RESPONSE GENERATION
    # ==========================================================

    def _generate_response(
        self,
        state: AgentState,
    ):

        # ModelRouter stores models as a list, so use the
        # canonical registry lookup.
        model = get_model_by_name(
            state.selected_model
        )

        prompt = self._build_prompt(
            state
        )

        state.response = (
            self.model_manager.generate(
                model=model,
                prompt=prompt,
            )
        )

        # Structured inference evidence.
        state.evidence.setdefault(
            "inference",
            [],
        ).append(
            {
                "conclusion": state.response,
                "supporting_evidence": {
                    "document": len(
                        state.evidence.get(
                            "document",
                            [],
                        )
                    ),
                    "vision": len(
                        state.evidence.get(
                            "vision",
                            [],
                        )
                    ),
                    "knowledge": len(
                        state.evidence.get(
                            "knowledge",
                            [],
                        )
                    ),
                },
            }
        )

        state.add_event(
            "generation",
            "complete",
            model=model.name,
        )

    # ==========================================================
    # PROMPT
    # ==========================================================

    def _build_prompt(
        self,
        state: AgentState,
    ) -> str:

        sections = [
            "You are operating inside a sovereign local AI "
            "workbench.",
            "",
            "USER REQUEST:",
            state.user_input,
            "",
            "EVIDENCE DISCIPLINE:",
            "Information available to you is divided into "
            "distinct evidence categories.",
            "",
            "DOCUMENT EVIDENCE:",
            "Information extracted from the supplied document.",
            "",
            "VISION EVIDENCE:",
            "Observations made from supplied images or rendered "
            "document pages. Vision observations may be uncertain.",
            "",
            "PRIVATE KNOWLEDGE EVIDENCE:",
            "Information retrieved from the private organizational "
            "knowledge base. This is internal reference material "
            "and must not be presented as direct observation of "
            "the current equipment or document.",
            "",
            "INFERENCE:",
            "Reasoning derived from the available evidence. "
            "Clearly distinguish inference from directly observed "
            "or documented facts.",
            "",
            "Do not convert an inference into a document fact.",
            "Do not claim that physical equipment is healthy, "
            "operating correctly, safe, compliant, or within "
            "specification unless the supplied evidence actually "
            "establishes that.",
            "Do not convert an unresolved verification item into "
            "a claim that equipment is unsafe, failed, non-compliant, "
            "or incapable of operation unless the evidence explicitly "
            "supports that conclusion.",
            "When a source says verification is pending, describe "
            "the status as unverified or pending verification.",
            "If evidence is insufficient, explicitly state that "
            "verification is required.",
        ]

        # ------------------------------------------------------
        # Structured evidence
        # ------------------------------------------------------

        if state.evidence.get(
            "document"
        ):

            sections.extend(
                [
                    "",
                    "STRUCTURED DOCUMENT EVIDENCE:",
                    str(
                        state.evidence[
                            "document"
                        ]
                    ),
                ]
            )

        if state.evidence.get(
            "vision"
        ):

            sections.extend(
                [
                    "",
                    "STRUCTURED VISION EVIDENCE:",
                    str(
                        state.evidence[
                            "vision"
                        ]
                    ),
                ]
            )

        if state.evidence.get(
            "knowledge"
        ):

            sections.extend(
                [
                    "",
                    "STRUCTURED PRIVATE KNOWLEDGE EVIDENCE:",
                    str(
                        state.evidence[
                            "knowledge"
                        ]
                    ),
                ]
            )

        # ------------------------------------------------------
        # Existing tool context
        # ------------------------------------------------------

        if state.vision_context:

            sections.extend(
                [
                    "",
                    "VISUAL ANALYSIS:",
                    str(
                        state.vision_context
                    ),
                ]
            )

        if state.knowledge_context:

            sections.extend(
                [
                    "",
                    "PRIVATE ORGANIZATIONAL KNOWLEDGE:",
                    str(
                        state.knowledge_context
                    ),
                ]
            )

        if "documents" in state.tool_results:

            sections.extend(
                [
                    "",
                    "DOCUMENT PROCESSING RESULT:",
                    str(
                        state.tool_results[
                            "documents"
                        ]
                    ),
                ]
            )

        if "calculator" in state.tool_results:

            sections.extend(
                [
                    "",
                    "CALCULATOR RESULT:",
                    str(
                        state.tool_results[
                            "calculator"
                        ]
                    ),
                ]
            )

        if "python" in state.tool_results:

            sections.extend(
                [
                    "",
                    "PYTHON EXECUTION RESULT:",
                    str(
                        state.tool_results[
                            "python"
                        ]
                    ),
                ]
            )

        if "code_execution" in state.tool_results:

            sections.extend(
                [
                    "",
                    "CODE EXECUTION RESULT:",
                    str(
                        state.tool_results[
                            "code_execution"
                        ]
                    ),
                ]
            )

        sections.extend(
            [
                "",
                "FINAL RESPONSE REQUIREMENTS:",
                "Use provided evidence as the basis for your answer.",
                "Do not invent missing information.",
                "Distinguish documented facts from visual observations.",
                "Distinguish organizational guidance from observations.",
                "Clearly identify uncertainty.",
                "Do not overstate conclusions.",
                "When evidence is insufficient, state what must be "
                "verified.",
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

        expression = text.strip()

        prefixes = [
            "calculate",
            "compute",
            "what is",
            "how much is",
        ]

        lower = expression.lower()

        for prefix in prefixes:

            if lower.startswith(
                prefix
            ):

                expression = expression[
                    len(prefix):
                ].strip()

                break

        return expression.rstrip(
            "?"
        ).strip()
