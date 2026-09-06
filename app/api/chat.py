from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agent.orchestrator import AgentOrchestrator

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    file_path: str | None = None
    has_image: bool = False
    image_path: str | None = None


def _serialize_state(state):
    return {
        "completed": state.completed,
        "error": state.error,
        "selected_model": state.selected_model,
        "routing_score": state.routing_score,
        "routing_reason": state.routing_reason,
        "response": state.response,
        "vision_context": state.vision_context,
        "knowledge_context": state.knowledge_context,
        "tool_results": state.tool_results,
        "metadata": state.metadata,
        "events": state.events,
    }


@router.post("")
async def chat(request: ChatRequest):
    """Execute a sovereign local workflow for a user message."""
    try:
        agent = AgentOrchestrator()
        state = agent.run(
            user_input=request.message,
            has_image=request.has_image,
            image_path=request.image_path,
            file_path=request.file_path,
        )

        task_id = uuid4().hex
        payload = _serialize_state(state)
        payload["task_id"] = task_id

        return {
            "status": "success" if state.completed else "error",
            "task_id": task_id,
            "selected_model": state.selected_model,
            "response": state.response,
            "completed": state.completed,
            "error": state.error,
            "tool_results": state.tool_results,
            "metadata": state.metadata,
            "events": state.events,
            "routing_reason": state.routing_reason,
            "vision_context": state.vision_context,
        }
    except Exception as exc:  # pragma: no cover - defensive API guard
        raise HTTPException(status_code=500, detail=str(exc)) from exc
