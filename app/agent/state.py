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

    # Multimodal / RAG context
    vision_context: Optional[str] = None
    knowledge_context: List[Dict[str, Any]] = field(
        default_factory=list
    )

    # Tool execution results
    tool_results: Dict[str, Any] = field(
        default_factory=dict
    )

    # General metadata for UI and audit
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )
    evidence: Dict[str, List[Dict[str, Any]]] = field(
        default_factory=lambda: {
            "document": [],
            "vision": [],
            "knowledge": [],
            "inference": [],
        }
    )
    # Execution trace
    events: List[Dict[str, Any]] = field(
        default_factory=list
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