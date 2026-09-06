from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agent.orchestrator import AgentOrchestrator
from app.api.models import TaskCreate, TaskResponse


router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)


TASK_STORE: dict[str, dict[str, Any]] = {}


class TaskRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
    )
    file_path: str | None = None
    has_image: bool = False
    image_path: str | None = None


# ==========================================================
# EXISTING AGENT WORKFLOW
# ==========================================================


@router.get("")
def list_tasks():
    """Return the current in-memory task list."""

    tasks = []

    for task_id, payload in TASK_STORE.items():
        tasks.append(
            {
                "task_id": task_id,
                **payload,
            }
        )

    return {
        "count": len(tasks),
        "tasks": tasks,
    }


@router.get("/{task_id}")
def get_task(task_id: str):
    """Fetch a single task by ID."""

    task = TASK_STORE.get(task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    return task


@router.post("")
async def create_task(request: TaskRequest):
    """Create and execute a task using the local agent workflow."""

    try:
        agent = AgentOrchestrator()

        state = agent.run(
            user_input=request.message,
            has_image=request.has_image,
            image_path=request.image_path,
            file_path=request.file_path,
        )

        task_id = uuid4().hex

        task_payload = {
            "status": (
                "success"
                if state.completed
                else "error"
            ),
            "selected_model": state.selected_model,
            "response": state.response,
            "completed": state.completed,
            "error": state.error,
            "tool_results": state.tool_results,
            "metadata": state.metadata,
            "events": state.events,
            "routing_reason": state.routing_reason,
        }

        TASK_STORE[task_id] = task_payload

        return {
            "task_id": task_id,
            **task_payload,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


# ==========================================================
# UI-FRIENDLY TASK START ENDPOINT
# ==========================================================


@router.post(
    "/start",
    response_model=TaskResponse,
)
async def start_task(
    task_request: TaskCreate,
):
    """
    Start a task using the existing local agent workflow.

    This preserves the /tasks/start API expected by the UI
    while still using the real AgentOrchestrator rather than
    a mock response or fake database.
    """

    task_id = uuid4().hex

    TASK_STORE[task_id] = {
        "status": "running",
        "created_at": datetime.now(),
        "task_type": task_request.task_type,
        "prompt": task_request.prompt,
        "result": None,
    }

    try:
        agent = AgentOrchestrator()

        state = agent.run(
            user_input=task_request.prompt,
        )

        TASK_STORE[task_id].update(
            {
                "status": (
                    "success"
                    if state.completed
                    else "error"
                ),
                "result": state.response,
            }
        )

        return {
            "task_id": task_id,
            "status": TASK_STORE[task_id]["status"],
            "created_at": TASK_STORE[task_id]["created_at"],
            "result": state.response,
            "artifacts": (
                [state.metadata["artifact_path"]]
                if state.metadata.get("artifact_path")
                else None
            ),
        }

    except Exception as exc:
        TASK_STORE[task_id].update(
            {
                "status": "error",
                "result": str(exc),
            }
        )

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc