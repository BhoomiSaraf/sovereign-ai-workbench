from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agent.orchestrator import AgentOrchestrator
from app.agent.state import AgentState
from app.api.files import IMAGE_EXTENSIONS, UPLOAD_DIRECTORY
from app.api.models import TaskCreate, TaskResponse
from app.database import (
    get_task,
    init_db,
    insert_audit_log,
    insert_task,
    list_tasks,
    update_task,
)
from app.security.audit import get_audit_logger


router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)

# Initialise the SQLite schema on first import.
init_db()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _resolve_uploaded_file(file_id: str) -> Path | None:
    """
    Resolve a file_id (returned by POST /files/upload) back to the
    file it was saved under, without needing to know the extension.
    """
    matches = list(UPLOAD_DIRECTORY.glob(f"{file_id}.*"))
    return matches[0] if matches else None


def _log_task_events(task_id: str, state: AgentState) -> None:
    """
    Mirror the agent's in-memory execution trace (state.events) into
    both the append-only JSONL audit log AND the SQLite audit_logs
    table so every source of truth stays consistent.
    """
    audit = get_audit_logger()

    for event in state.events:
        details = {
            key: value
            for key, value in event.items()
            if key not in ("type", "status")
        }

        # JSONL file (existing behaviour — keep intact)
        audit.record(
            event["type"].upper(),
            status=event["status"],
            task_id=task_id,
            **details,
        )

        # SQLite audit_logs table (new)
        insert_audit_log(
            event_type=event["type"].upper(),
            task_id=task_id,
            details={"status": event["status"], **details},
        )


# ---------------------------------------------------------------------------
# Request schema for the legacy POST /tasks endpoint
# ---------------------------------------------------------------------------


class TaskRequest(BaseModel):
    message: str = Field(..., min_length=1)
    file_path: str | None = None
    has_image: bool = False
    image_path: str | None = None


# ===========================================================================
# LEGACY AGENT WORKFLOW  (POST /tasks  +  GET /tasks  +  GET /tasks/{id})
# ===========================================================================


@router.get("")
def list_tasks_endpoint():
    """Return all persisted tasks, newest first."""
    rows = list_tasks()
    return {"count": len(rows), "tasks": rows}


@router.get("/{task_id}")
def get_task_endpoint(task_id: str):
    """Fetch a single task by ID from SQLite."""
    task = get_task(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


@router.post("")
async def create_task(request: TaskRequest):
    """Create and execute a task using the local agent workflow."""
    task_id = uuid4().hex
    now = datetime.now(timezone.utc)
    audit = get_audit_logger()

    # Persist task row immediately so GET /tasks/{id} works right away.
    insert_task(
        task_id=task_id,
        task_type="chat",
        prompt=request.message,
        created_at=now,
    )

    # SQLite audit entry
    insert_audit_log(
        event_type="TASK_STARTED",
        task_id=task_id,
        details={"message": request.message},
    )

    # JSONL audit entry (existing behaviour)
    audit.record("TASK_STARTED", task_id=task_id, message=request.message)

    try:
        agent = AgentOrchestrator()

        state = agent.run(
            user_input=request.message,
            has_image=request.has_image,
            image_path=request.image_path,
            file_path=request.file_path,
        )

        _log_task_events(task_id, state)

        final_status = "success" if state.completed else "error"
        artifacts: list[str] = []
        if state.metadata.get("artifact_path"):
            artifacts = [state.metadata["artifact_path"]]

        update_task(
            task_id=task_id,
            status=final_status,
            result=state.response,
            model=state.selected_model,
            artifacts=artifacts,
        )

        completion_event = (
            "TASK_COMPLETED" if state.completed else "TASK_FAILED"
        )

        insert_audit_log(
            event_type=completion_event,
            task_id=task_id,
            details={
                "status": final_status,
                "selected_model": state.selected_model,
                "error": state.error,
            },
        )
        audit.record(
            completion_event,
            status=final_status,
            task_id=task_id,
            selected_model=state.selected_model,
            error=state.error,
        )

        return {
            "task_id": task_id,
            "status": final_status,
            "selected_model": state.selected_model,
            "response": state.response,
            "completed": state.completed,
            "error": state.error,
            "tool_results": state.tool_results,
            "metadata": state.metadata,
            "events": state.events,
            "routing_reason": state.routing_reason,
        }

    except Exception as exc:
        update_task(task_id=task_id, status="error", result=str(exc))

        insert_audit_log(
            event_type="TASK_FAILED",
            task_id=task_id,
            details={"status": "error", "error": str(exc)},
        )
        audit.record(
            "TASK_FAILED",
            status="error",
            task_id=task_id,
            error=str(exc),
        )

        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ===========================================================================
# UI-FRIENDLY START ENDPOINT  (POST /tasks/start)
# ===========================================================================


@router.post(
    "/start",
    response_model=TaskResponse,
)
async def start_task(task_request: TaskCreate):
    """
    Start a task using the local agent workflow.

    Writes the task and an initial TASK_STARTED audit row to SQLite
    immediately, so the UI can poll GET /tasks/{task_id} and
    GET /audit/{task_id} from the moment the request is accepted.
    """
    task_id = uuid4().hex
    now = datetime.now(timezone.utc)
    audit = get_audit_logger()

    # ------------------------------------------------------------------
    # Resolve optional uploaded file
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Persist task row  — status starts as 'running'
    # ------------------------------------------------------------------
    insert_task(
        task_id=task_id,
        task_type=task_request.task_type,
        prompt=task_request.prompt,
        created_at=now,
    )

    # ------------------------------------------------------------------
    # Initial audit log row
    # ------------------------------------------------------------------
    insert_audit_log(
        event_type="TASK_STARTED",
        task_id=task_id,
        details={
            "task_type": task_request.task_type,
            "prompt": task_request.prompt,
            "file_id": task_request.file_id,
        },
        timestamp=now,
    )

    # JSONL file (existing behaviour)
    audit.record(
        "TASK_STARTED",
        task_id=task_id,
        task_type=task_request.task_type,
        prompt=task_request.prompt,
        file_id=task_request.file_id,
    )

    # ------------------------------------------------------------------
    # Run agent
    # ------------------------------------------------------------------
    try:
        agent = AgentOrchestrator()

        state = agent.run(
            user_input=task_request.prompt,
            has_image=has_image,
            image_path=image_path,
            file_path=file_path,
        )

        _log_task_events(task_id, state)

        final_status = "success" if state.completed else "error"
        artifacts: list[str] = []
        if state.metadata.get("artifact_path"):
            artifacts = [state.metadata["artifact_path"]]

        update_task(
            task_id=task_id,
            status=final_status,
            result=state.response,
            model=state.selected_model,
            artifacts=artifacts,
            completed_at=datetime.now(timezone.utc),
        )

        completion_event = (
            "TASK_COMPLETED" if state.completed else "TASK_FAILED"
        )

        insert_audit_log(
            event_type=completion_event,
            task_id=task_id,
            details={
                "status": final_status,
                "selected_model": state.selected_model,
                "error": state.error,
            },
        )
        audit.record(
            completion_event,
            status=final_status,
            task_id=task_id,
            selected_model=state.selected_model,
            error=state.error,
        )

        # Re-fetch so the response reflects exactly what is in the DB.
        persisted = get_task(task_id)

        return TaskResponse(
            task_id=task_id,
            status=persisted["status"],
            created_at=datetime.fromisoformat(persisted["created_at"]),
            result=persisted["result"],
            artifacts=persisted.get("artifacts") or [],
        )

    except Exception as exc:
        update_task(
            task_id=task_id,
            status="error",
            result=str(exc),
            completed_at=datetime.now(timezone.utc),
        )

        insert_audit_log(
            event_type="TASK_FAILED",
            task_id=task_id,
            details={"status": "error", "error": str(exc)},
        )
        audit.record(
            "TASK_FAILED",
            status="error",
            task_id=task_id,
            error=str(exc),
        )

        raise HTTPException(status_code=500, detail=str(exc)) from exc
