"""
app/api/audit.py

Audit trail endpoints for the Sovereign AI Workbench.

Two sources of truth are exposed:
  - GET /audit/recent      — last N entries from the append-only JSONL file
                             (existing behaviour, kept intact)
  - GET /audit/{task_id}  — all SQLite audit_logs rows for one task,
                             ordered oldest-first, to power the UI's
                             workflow progress tracker
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.database import get_audit_logs_for_task
from app.security.audit import get_audit_logger


router = APIRouter(
    prefix="/audit",
    tags=["audit"],
)


# ---------------------------------------------------------------------------
# Existing endpoint — JSONL-backed recent events feed
# ---------------------------------------------------------------------------


@router.get("/recent")
def recent_audit_events(
    limit: int = Query(100, ge=1, le=1000),
) -> dict[str, Any]:
    """
    Return the most recent audit log entries from the local JSONL file.

    This feed covers the entire workbench (all tasks), newest-last,
    and is capped by `limit`.
    """
    events = get_audit_logger().read_recent(limit=limit)

    return {
        "count": len(events),
        "events": events,
    }


# ---------------------------------------------------------------------------
# New endpoint — SQLite-backed per-task audit trail
# ---------------------------------------------------------------------------


@router.get("/{task_id}")
def get_task_audit_trail(task_id: str) -> dict[str, Any]:
    """
    Return the complete audit trail for a single task, ordered by
    timestamp ascending (oldest event first).

    Each entry contains:
      - id          — auto-increment row id
      - task_id     — echoed back for convenience
      - timestamp   — ISO-8601 UTC string
      - event_type  — e.g. TASK_STARTED, MODEL_SELECTED, TASK_COMPLETED
      - details     — structured dict with event-specific context

    A 404 is raised only when the task_id has no audit rows at all,
    which indicates the task never reached the database.

    Typical event sequence for a successful run:
        TASK_STARTED → MODEL_SELECTED → [tool events] → TASK_COMPLETED
    """
    rows = get_audit_logs_for_task(task_id)

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No audit trail found for task '{task_id}'.",
        )

    return {
        "task_id": task_id,
        "count": len(rows),
        "events": rows,
    }
