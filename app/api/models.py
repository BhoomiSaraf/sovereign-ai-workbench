from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.router.model_registry import get_available_models
from app.router.model_router import ModelRouter

router = APIRouter(prefix="/models", tags=["models"])


@router.get("")
def list_models():
    """Return the locally registered model catalog."""
    models = []
    for model in get_available_models():
        models.append(
            {
                "name": model.name,
                "ollama_name": model.ollama_name,
                "capabilities": model.capabilities,
                "modalities": model.modalities,
                "priority": model.priority,
            }
        )

    return {"count": len(models), "models": models}


@router.get("/route")
def route_model(
    task: str = Query(..., min_length=1),
    has_image: bool = False,
):
    """Return the router decision for a provided prompt."""
    try:
        decision = ModelRouter().route(task=task, has_image=has_image)
        return {
            "task": task,
            "has_image": has_image,
            "selected_model": decision.model.name,
            "score": decision.score,
            "matched_capabilities": decision.matched_capabilities,
            "reason": decision.reason,
            "task_requirements": {
                "capabilities": decision.task_requirements.capabilities,
                "modalities": decision.task_requirements.modalities,
                "complexity": decision.task_requirements.complexity,
                "rag_required": decision.task_requirements.rag_required,
            },
        }
    except Exception as exc:  # pragma: no cover - defensive API guard
        raise HTTPException(status_code=400, detail=str(exc)) from exc
