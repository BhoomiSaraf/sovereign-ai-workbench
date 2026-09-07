from fastapi import APIRouter, Query

from app.security.audit import get_audit_logger


router = APIRouter(
    prefix="/audit",
    tags=["audit"],
)


@router.get("/recent")
def recent_audit_events(
    limit: int = Query(100, ge=1, le=1000),
):
    """Return the most recent local audit log entries."""

    events = get_audit_logger().read_recent(limit=limit)

    return {
        "count": len(events),
        "events": events,
    }
