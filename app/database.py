"""
app/database.py

Local SQLite persistence layer for the Sovereign AI Workbench.

All data stays on-device at data/app.db.
No ORM, no network, standard library sqlite3 only.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

_ROOT = Path(__file__).resolve().parents[1]
_DB_PATH = _ROOT / "data" / "app.db"

# ---------------------------------------------------------------------------
# Connection pool (one per thread — sqlite3 connections are not thread-safe)
# ---------------------------------------------------------------------------

_local = threading.local()


def _get_connection() -> sqlite3.Connection:
    """
    Return a per-thread SQLite connection.

    Row factory is set so rows behave like dicts when accessed by column name.
    WAL journal mode gives better concurrent read performance.
    Foreign-key enforcement is enabled for correctness.
    """
    if not hasattr(_local, "conn") or _local.conn is None:
        _DB_PATH.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(
            str(_DB_PATH),
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        _local.conn = conn

    return _local.conn


# ---------------------------------------------------------------------------
# Schema initialisation
# ---------------------------------------------------------------------------

_TASKS_DDL = """
CREATE TABLE IF NOT EXISTS tasks (
    id           TEXT      PRIMARY KEY,
    status       TEXT      NOT NULL DEFAULT 'running',
    created_at   TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    task_type    TEXT,
    prompt       TEXT,
    model        TEXT,
    result       TEXT,
    artifacts    TEXT      -- JSON array of artifact paths
);
"""

_AUDIT_LOGS_DDL = """
CREATE TABLE IF NOT EXISTS audit_logs (
    id         INTEGER   PRIMARY KEY AUTOINCREMENT,
    task_id    TEXT,
    timestamp  TIMESTAMP NOT NULL,
    event_type TEXT      NOT NULL,
    details    TEXT      -- free-form JSON blob
);
"""

_AUDIT_IDX_DDL = """
CREATE INDEX IF NOT EXISTS idx_audit_logs_task_id
    ON audit_logs (task_id, timestamp ASC);
"""


def init_db() -> None:
    """
    Create all application tables if they do not already exist.

    Safe to call on every startup — uses CREATE IF NOT EXISTS throughout.
    """
    conn = _get_connection()
    with conn:
        conn.execute(_TASKS_DDL)
        conn.execute(_AUDIT_LOGS_DDL)
        conn.execute(_AUDIT_IDX_DDL)


# ---------------------------------------------------------------------------
# Generic query helpers
# ---------------------------------------------------------------------------


def execute_query(sql: str, params: tuple = ()) -> None:
    """
    Execute a write statement (INSERT / UPDATE / DELETE).

    The statement is executed inside an implicit transaction;
    changes are committed before returning.
    """
    conn = _get_connection()
    with conn:
        conn.execute(sql, params)


def fetch_one(sql: str, params: tuple = ()) -> dict[str, Any] | None:
    """
    Return the first matching row as a plain dict, or None.
    """
    conn = _get_connection()
    cursor = conn.execute(sql, params)
    row = cursor.fetchone()
    return dict(row) if row is not None else None


def fetch_all(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    """
    Return all matching rows as a list of plain dicts.
    """
    conn = _get_connection()
    cursor = conn.execute(sql, params)
    return [dict(row) for row in cursor.fetchall()]


# ---------------------------------------------------------------------------
# Task helpers
# ---------------------------------------------------------------------------


def insert_task(
    task_id: str,
    task_type: str,
    prompt: str,
    created_at: datetime | None = None,
) -> None:
    """
    Insert a new task row with status='running'.
    """
    ts = (created_at or datetime.now(timezone.utc)).isoformat()
    execute_query(
        """
        INSERT INTO tasks (id, status, created_at, task_type, prompt)
        VALUES (?, ?, ?, ?, ?)
        """,
        (task_id, "running", ts, task_type, prompt),
    )


def update_task(
    task_id: str,
    status: str,
    result: str | None = None,
    model: str | None = None,
    artifacts: list[str] | None = None,
    completed_at: datetime | None = None,
) -> None:
    """
    Update a task row after the agent finishes (or fails).
    """
    ts = (completed_at or datetime.now(timezone.utc)).isoformat()
    artifacts_json = json.dumps(artifacts or [])
    execute_query(
        """
        UPDATE tasks
           SET status       = ?,
               completed_at = ?,
               result       = ?,
               model        = ?,
               artifacts    = ?
         WHERE id = ?
        """,
        (status, ts, result, model, artifacts_json, task_id),
    )


def get_task(task_id: str) -> dict[str, Any] | None:
    """
    Fetch a single task by primary key.
    Deserialises the artifacts JSON column automatically.
    """
    row = fetch_one(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,),
    )
    if row and row.get("artifacts"):
        try:
            row["artifacts"] = json.loads(row["artifacts"])
        except (json.JSONDecodeError, TypeError):
            row["artifacts"] = []
    return row


def list_tasks() -> list[dict[str, Any]]:
    """Return all tasks ordered by creation time descending."""
    rows = fetch_all(
        "SELECT * FROM tasks ORDER BY created_at DESC"
    )
    for row in rows:
        if row.get("artifacts"):
            try:
                row["artifacts"] = json.loads(row["artifacts"])
            except (json.JSONDecodeError, TypeError):
                row["artifacts"] = []
    return rows


# ---------------------------------------------------------------------------
# Audit log helpers
# ---------------------------------------------------------------------------


def insert_audit_log(
    event_type: str,
    task_id: str | None = None,
    details: dict[str, Any] | None = None,
    timestamp: datetime | None = None,
) -> None:
    """
    Append one row to audit_logs.

    `details` is serialised to JSON so the column stays queryable.
    """
    ts = (timestamp or datetime.now(timezone.utc)).isoformat()
    details_json = json.dumps(details or {}, default=str)
    execute_query(
        """
        INSERT INTO audit_logs (task_id, timestamp, event_type, details)
        VALUES (?, ?, ?, ?)
        """,
        (task_id, ts, event_type, details_json),
    )


def get_audit_logs_for_task(task_id: str) -> list[dict[str, Any]]:
    """
    Return all audit rows for a task, oldest first.
    Deserialises the details JSON column automatically.
    """
    rows = fetch_all(
        """
        SELECT id, task_id, timestamp, event_type, details
          FROM audit_logs
         WHERE task_id = ?
         ORDER BY timestamp ASC
        """,
        (task_id,),
    )
    for row in rows:
        if row.get("details"):
            try:
                row["details"] = json.loads(row["details"])
            except (json.JSONDecodeError, TypeError):
                pass
    return rows
