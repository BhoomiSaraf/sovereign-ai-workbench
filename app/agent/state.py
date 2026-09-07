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
