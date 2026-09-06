from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


class AuditLogger:
    """
    Append-only local audit logger.

    No network calls.
    No external logging service.
    """

    def __init__(self, log_path: str = "logs/audit.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def record(
        self,
        event_type: str,
        status: str = "success",
        *,
        task_id: Optional[str] = None,
        **details: Any,
    ) -> Dict[str, Any]:

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "status": status,
            "task_id": task_id,
            "details": details,
        }

        with self._lock:
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")

        return event

    def read_recent(self, limit: int = 100) -> list[Dict[str, Any]]:
        if not self.log_path.exists():
            return []

        with self.log_path.open("r", encoding="utf-8") as f:
            lines = f.readlines()

        events = []

        for line in lines[-limit:]:
            line = line.strip()

            if not line:
                continue

            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue

        return events