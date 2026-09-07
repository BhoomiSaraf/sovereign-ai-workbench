from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agent.orchestrator import AgentOrchestrator
from app.agent.state import AgentState
from app.api.files import IMAGE_EXTENSIONS, UPLOAD_DIRECTORY
from app.api.models import TaskCreate, TaskResponse
from app.security.audit import get_audit_logger


router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)


TASK_STORE: dict[str, dict[str, Any]] = {}


def _resolve_uploaded_file(file_id: str) -> Path | None:
    """
    Resolve a file_id (returned by POST /files/upload) back to the
    file it saved, without needing to know the extension.
    """

    matches = list(UPLOAD_DIRECTORY.glob(f"{file_id}.*"))
    return matches[0] if matches else None


def _log_task_events(
    task_id: str,
    state: AgentState,
) -> None:
    """
    Mirror the agent's in-memory execution trace (state.events) into
    the local append-only audit log, so /audit/recent reflects the
    same steps the UI's execution trace shows.
    """

    audit = get_audit_logger()

    for event in state.events:
        details = {
            key: value
            for key, value in event.items()
            if key not in ("type", "status")
        }

        audit.record(
            event["type"].upper(),
            status=event["status"],
            task_id=task_id,
            **details,
        )


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

    task_id = uuid4().hex
    audit = get_audit_logger()

    audit.record(
        "TASK_STARTED",
        task_id=task_id,
        message=request.message,
    )

    try:
        agent = AgentOrchestrator()

        state = agent.run(
            user_input=request.message,
            has_image=request.has_image,
            image_path=request.image_path,
            file_path=request.file_path,
        )

        _log_task_events(task_id, state)

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

        audit.record(
            "TASK_COMPLETED" if state.completed else "TASK_FAILED",
            status="success" if state.completed else "error",
            task_id=task_id,
            selected_model=state.selected_model,
            error=state.error,
        )

        return {
            "task_id": task_id,
            **task_payload,
        }

    except Exception as exc:
        audit.record(
            "TASK_FAILED",
            status="error",
            task_id=task_id,
            error=str(exc),
        )

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
    audit = get_audit_logger()

    # Resolve an uploaded file_id (from POST /files/upload) back to
    # the path it was saved under, and route it as a document or an
    # image depending on its extension.
    file_path: str | None = None
    image_path: str | None = None
    has_image = False

    if task_request.file_id:
        resolved = _resolve_uploaded_file(task_request.file_id)

        if resolved is None:
            raise HTTPException(
                status_code=404,
                detail=f"Uploaded file '{task_request.file_id}' was not found.",
            )

        if resolved.suffix.lower() in IMAGE_EXTENSIONS:
            has_image = True
            image_path = str(resolved)
        else:
            file_path = str(resolved)

    TASK_STORE[task_id] = {
        "status": "running",
        "created_at": datetime.now(),
        "task_type": task_request.task_type,
        "prompt": task_request.prompt,
        "result": None,
    }

    audit.record(
        "TASK_STARTED",
        task_id=task_id,
        task_type=task_request.task_type,
        prompt=task_request.prompt,
        file_id=task_request.file_id,
    )

    try:
        agent = AgentOrchestrator()

        state = agent.run(
            user_input=task_request.prompt,
            has_image=has_image,
            image_path=image_path,
            file_path=file_path,
        )

        _log_task_events(task_id, state)

        TASK_STORE[task_id].update(
            {
                "status": (
                    "success"
                    if state.completed
                    else "error"
                ),
                "result": state.response,
                "metadata": state.metadata,
                "events": state.events,
                "selected_model": state.selected_model,
            }
        )

        audit.record(
            "TASK_COMPLETED" if state.completed else "TASK_FAILED",
            status="success" if state.completed else "error",
            task_id=task_id,
            selected_model=state.selected_model,
            error=state.error,
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

        audit.record(
            "TASK_FAILED",
            status="error",
            task_id=task_id,
            error=str(exc),
        )

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc