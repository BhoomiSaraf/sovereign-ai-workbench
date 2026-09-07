$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Sovereign AI Workbench - Group 2 Core" -ForegroundColor Cyan
Write-Host " Iterative Agent + Workspace + Validation" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$Root = Get-Location

function Write-ProjectFile {
    param(
        [string]$RelativePath,
        [string]$Content
    )

    $Path = Join-Path $Root $RelativePath
    $Directory = Split-Path $Path -Parent

    if (!(Test-Path $Directory)) {
        New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    }

    Set-Content -Path $Path -Value $Content -Encoding UTF8

    Write-Host "Updated: $RelativePath" -ForegroundColor Green
}

# ============================================================
# 1. AgentState
# ============================================================

Write-ProjectFile "app/agent/state.py" @'
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AgentState:
    user_input: str

    has_image: bool = False
    image_path: Optional[str] = None

    selected_model: Optional[str] = None
    routing_score: Optional[float] = None
    routing_reason: List[str] = field(default_factory=list)

    response: Optional[str] = None
    task_requirements: Optional[Any] = None
    vision_context: Optional[str] = None
    knowledge_context: List[Dict[str, Any]] = field(default_factory=list)

    tool_results: Dict[str, Any] = field(default_factory=dict)

    metadata: Dict[str, Any] = field(default_factory=dict)

    evidence: Dict[str, List[Dict[str, Any]]] = field(
        default_factory=lambda: {
            "document": [],
            "vision": [],
            "knowledge": [],
            "inference": [],
        }
    )

    events: List[Dict[str, Any]] = field(default_factory=list)

    current_step: Optional[str] = None
    completed_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)

    iteration: int = 0
    max_iterations: int = 8

    retry_counts: Dict[str, int] = field(
        default_factory=dict
    )

    observations: List[Dict[str, Any]] = field(
        default_factory=list
    )

    decision: Optional[str] = None

    status: str = "initialized"

    validation: Dict[str, Any] = field(
        default_factory=dict
    )

    completed: bool = False
    error: Optional[str] = None

    def add_event(
        self,
        event_type: str,
        status: str,
        **details: Any,
    ) -> None:

        event = {
            "type": event_type,
            "status": status,
        }

        if details:
            event.update(details)

        self.events.append(event)

    def observe(
        self,
        step: str,
        success: bool,
        **details: Any,
    ) -> None:

        observation = {
            "iteration": self.iteration,
            "step": step,
            "success": success,
            **details,
        }

        self.observations.append(
            observation
        )

        self.add_event(
            "observation",
            "complete" if success else "failed",
            **observation,
        )

    def begin_iteration(self) -> bool:

        if self.iteration >= self.max_iterations:
            return False

        self.iteration += 1

        self.add_event(
            "iteration",
            "start",
            iteration=self.iteration,
            max_iterations=self.max_iterations,
        )

        return True

    def mark_step_complete(
        self,
        step: str,
    ) -> None:

        if step not in self.completed_steps:
            self.completed_steps.append(step)

        self.failed_steps = [
            item
            for item in self.failed_steps
            if item != step
        ]

    def mark_step_failed(
        self,
        step: str,
    ) -> None:

        if step not in self.failed_steps:
            self.failed_steps.append(step)

        self.retry_counts[step] = (
            self.retry_counts.get(step, 0) + 1
        )

    def can_retry(
        self,
        step: str,
        limit: int = 1,
    ) -> bool:

        return (
            self.retry_counts.get(step, 0)
            < limit
        )

    def can_continue(self) -> bool:

        return (
            self.iteration
            < self.max_iterations
        )
'@

# ============================================================
# 2. Agent Validator
# ============================================================

Write-ProjectFile "app/agent/validator.py" @'
from typing import Any


class AgentValidator:
    """
    Deterministic final validation gate.

    No network calls and no second router/model are used here.
    """

    def validate_response(
        self,
        state,
    ) -> tuple[bool, str]:

        if state.response is None:
            return (
                False,
                "No response was generated.",
            )

        if not str(state.response).strip():
            return (
                False,
                "Generated response is empty.",
            )

        return (
            True,
            "Response is non-empty.",
        )

    def validate_evidence(
        self,
        state,
    ) -> tuple[bool, str]:

        requirements = (
            state.task_requirements
        )

        if requirements is None:
            return (
                True,
                "No explicit evidence requirement.",
            )

        required = []

        if getattr(
            requirements,
            "needs_document",
            False,
        ):
            required.append("document")

        if getattr(
            requirements,
            "needs_vision",
            False,
        ):
            required.append("vision")

        if getattr(
            requirements,
            "needs_knowledge",
            False,
        ):
            required.append("knowledge")

        missing = [
            source
            for source in required
            if not state.evidence.get(source)
        ]

        if missing:
            return (
                False,
                "Missing evidence: "
                + ", ".join(missing),
            )

        return (
            True,
            "Evidence requirements satisfied.",
        )

    def validate_artifact(
        self,
        state,
    ) -> tuple[bool, str]:

        result = state.tool_results.get(
            "artifact"
        )

        if result is None:
            return (
                True,
                "No artifact requested.",
            )

        if hasattr(result, "get"):

            if result.get("success") is False:
                return (
                    False,
                    result.get(
                        "error",
                        "Artifact generation failed.",
                    ),
                )

            validation = result.get(
                "validation"
            )

            if isinstance(
                validation,
                dict,
            ):

                if validation.get(
                    "valid"
                ) is False:
                    return (
                        False,
                        "Artifact validation failed.",
                    )

        return (
            True,
            "Artifact validation passed.",
        )

    def validate_code(
        self,
        state,
    ) -> tuple[bool, str]:

        result = state.tool_results.get(
            "python"
        )

        if result is None:
            return (
                True,
                "No Python execution requested.",
            )

        if hasattr(result, "get"):

            if result.get("success") is False:

                error = (
                    result.get("error")
                    or result.get("stderr")
                    or "Python execution failed."
                )

                return (
                    False,
                    str(error),
                )

        return (
            True,
            "Code execution passed.",
        )

    def validate(
        self,
        state,
    ) -> dict[str, Any]:

        response_ok, response_message = (
            self.validate_response(state)
        )

        evidence_ok, evidence_message = (
            self.validate_evidence(state)
        )

        artifact_ok, artifact_message = (
            self.validate_artifact(state)
        )

        code_ok, code_message = (
            self.validate_code(state)
        )

        valid = all(
            [
                response_ok,
                evidence_ok,
                artifact_ok,
                code_ok,
            ]
        )

        return {
            "valid": valid,
            "response": {
                "success": response_ok,
                "message": response_message,
            },
            "evidence": {
                "success": evidence_ok,
                "message": evidence_message,
            },
            "artifact": {
                "success": artifact_ok,
                "message": artifact_message,
            },
            "code": {
                "success": code_ok,
                "message": code_message,
            },
        }
'@

# ============================================================
# 3. Orchestrator workspace initialization
# ============================================================

$OrchestratorPath = Join-Path $Root "app\agent\orchestrator.py"

$orchestrator = Get-Content `
    $OrchestratorPath `
    -Raw

if ($orchestrator -notmatch "TaskWorkspace") {

    $orchestrator = $orchestrator.Replace(
        "from app.tools.artifact import ArtifactTool",
        "from app.tools.artifact import ArtifactTool`r`nfrom app.security.workspace import TaskWorkspace`r`nfrom uuid import uuid4"
    )

    $oldState = @'
        state = AgentState(
            user_input=user_input,
            has_image=has_image,
            image_path=image_path,
        )
'@

    $newState = @'
        task_id = uuid4().hex

        workspace = TaskWorkspace(
            task_id=task_id
        )

        state = AgentState(
            user_input=user_input,
            has_image=has_image,
            image_path=image_path,
        )

        state.metadata["task_id"] = task_id
        state.metadata["workspace_root"] = str(
            workspace.root
        )
'@

    if ($orchestrator.Contains($oldState)) {
        $orchestrator = $orchestrator.Replace(
            $oldState,
            $newState
        )
    }

    Set-Content `
        -Path $OrchestratorPath `
        -Value $orchestrator `
        -Encoding UTF8

    Write-Host "Updated: app/agent/orchestrator.py" -ForegroundColor Green
}
else {
    Write-Host "Workspace initialization already exists." -ForegroundColor Yellow
}

# ============================================================
# 4. Replace AgentExecutor.execute()
# ============================================================

$ExecutorPath = Join-Path $Root "app\agent\executor.py"

$executor = Get-Content `
    $ExecutorPath `
    -Raw

$startMarker = "    def execute(`r`n"
$endMarker = "    # ==========================================================`r`n    # AGENT EXECUTION PROGRESS"

$startIndex = $executor.IndexOf(
    $startMarker
)

$endIndex = $executor.IndexOf(
    $endMarker
)

if (
    $startIndex -lt 0 -or
    $endIndex -lt 0 -or
    $endIndex -le $startIndex
) {
    throw "Could not locate AgentExecutor.execute() boundaries."
}

$newExecute = @'
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

                state.metadata["plan"] = plan

            # Validation is a mandatory terminal stage.
            if "validate" not in plan:
                plan.append("validate")

            state.metadata["plan"] = plan
            state.metadata["execution_mode"] = (
                "iterative_plan_driven"
            )

            state.status = "planning"

            state.add_event(
                "plan",
                "start",
                steps=list(plan),
            )

            remaining = list(plan)

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

        elif step == "python":

            if self._should_execute_python(state):
                self._execute_python_iterative(state)
            else:
                state.add_event(
                    "step",
                    "skipped",
                    step=step,
                    reason="Python execution not required.",
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

        if step == "python":

            result = state.tool_results.get(
                "python"
            )

            if result is None:
                return True

            if hasattr(result, "get"):
                return bool(
                    result.get(
                        "success",
                        False,
                    )
                )

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

        # Python gets an explicit repair loop.
        if step == "python":

            if state.can_retry(
                "python_repair",
                limit=2,
            ):

                state.mark_step_failed(
                    "python_repair"
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
            tool="python",
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
            reason="Python execution failed.",
            repair_attempt=state.retry_counts.get(
                "python_repair",
                0,
            ),
        )

        # Remove the failed Python step so it is executed again.
        state.completed_steps = [
            item
            for item in state.completed_steps
            if item != "python"
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
            )
'@

$part1 = $executor.Substring(0, $startIndex)
$part2 = $executor.Substring($endIndex)

$newExecutor = $part1 + $newExecute + $part2

Set-Content -Path $executorPath -Value $newExecutor -Encoding UTF8

Write-Host "Updated: app/agent/executor.py" -ForegroundColor Green

# ============================================================
# 5. Python tool: accept task workspace
# ============================================================

Write-ProjectFile "app/tools/python.py" @'
from app.security.sandbox import PythonSandbox
from app.tools.result import ToolResult


class PythonTool:

    name = "python"

    def __init__(
        self,
        sandbox=None,
    ):
        self.sandbox = (
            sandbox
            or PythonSandbox()
        )

    def execute(
        self,
        code: str,
        task_id: str | None = None,
        workspace_root: str | None = None,
    ) -> ToolResult:

        try:

            result = self.sandbox.execute(
                code,
                workspace_root=workspace_root,
            )

            return ToolResult(
                success=result.success,
                result=result.stdout,
                error=(
                    result.stderr
                    if not result.success
                    else None
                ),
                metadata={
                    "return_code": result.return_code,
                    "timed_out": result.timed_out,
                    "task_id": task_id,
                    "workspace_root": workspace_root,
                    "stderr": result.stderr,
                    "stdout": result.stdout,
                },
            )

        except Exception as exc:

            return ToolResult(
                success=False,
                result=None,
                error=str(exc),
                metadata={
                    "task_id": task_id,
                    "workspace_root": workspace_root,
                },
            )


class _PythonReplCompatibility:

    def __init__(
        self,
        tool=None,
    ):
        self.tool = tool or PythonTool()

    def invoke(
        self,
        payload,
    ):
        result = self.tool.execute(
            payload.get("code", "")
        )

        if result.success:
            return result.result or ""

        return result.error or ""


python_repl = _PythonReplCompatibility()
'@

# ============================================================
# 6. Sandbox workspace mounting
# ============================================================

$SandboxPath = Join-Path $Root "app\security\sandbox.py"

$sandbox = Get-Content `
    $SandboxPath `
    -Raw

if ($sandbox -notmatch "workspace_root") {

    $sandbox = $sandbox.Replace(
        "def execute(self, code: str) -> SandboxResult:",
        "def execute(self, code: str, workspace_root=None) -> SandboxResult:"
    )

    $sandbox = $sandbox.Replace(
        'with tempfile.TemporaryDirectory() as tmp:',
        'workspace_context = None`r`n`r`n        if workspace_root:`r`n            workspace_context = nullcontext(Path(workspace_root))`r`n        else:`r`n            workspace_context = tempfile.TemporaryDirectory()`r`n`r`n        with workspace_context as tmp:'
    )

    $sandbox = $sandbox.Replace(
        'workdir = Path(tmp)',
        'workdir = Path(tmp)'
    )

    Set-Content `
        -Path $SandboxPath `
        -Value $sandbox `
        -Encoding UTF8

    Write-Host "Updated: app/security/sandbox.py" -ForegroundColor Green
}
else {
    Write-Host "Sandbox workspace support already exists." -ForegroundColor Yellow
}

# ============================================================
# 7. Phase 3 tests
# ============================================================

Write-ProjectFile "tests/test_group2_core.py" @'
from pathlib import Path

from app.agent.state import AgentState
from app.security.workspace import (
    TaskWorkspace,
    WorkspaceSecurityError,
)


def test_state_supports_iterations():

    state = AgentState(
        user_input="test",
        max_iterations=2,
    )

    assert state.begin_iteration()
    assert state.iteration == 1

    state.observe(
        "python",
        False,
        error="NameError",
    )

    state.mark_step_failed(
        "python"
    )

    assert state.retry_counts[
        "python"
    ] == 1

    assert state.can_retry(
        "python",
        2,
    )

    assert state.begin_iteration()
    assert not state.begin_iteration()


def test_workspace_rejects_host_paths(
    tmp_path,
):

    workspace = TaskWorkspace(
        "task",
        tmp_path / "tasks",
    )

    try:
        workspace.resolve(
            r"C:\Users\aarohi\secret.txt"
        )
        assert False
    except WorkspaceSecurityError:
        pass


def test_workspace_rejects_traversal(
    tmp_path,
):

    workspace = TaskWorkspace(
        "task",
        tmp_path / "tasks",
    )

    try:
        workspace.resolve(
            "../../secret.txt"
        )
        assert False
    except WorkspaceSecurityError:
        pass
'@

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host " Group 2 Core implementation applied." -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Run tests now:"
Write-Host ""
Write-Host '  $env:PYTHONPATH = (Get-Location).Path'
Write-Host '  python -m pytest -q'
Write-Host ""