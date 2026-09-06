from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.router.model_registry import get_available_models
from app.router.model_router import ModelRouter


router = APIRouter(
    prefix="/models",
    tags=["models"],
)


# ==========================================================
# API SCHEMAS
# ==========================================================


class TaskCreate(BaseModel):
    task_type: str = Field(
        ...,
        description="Task type, for example coding or document_analysis.",
    )
    prompt: str = Field(
        ...,
        description="The user's instruction.",
    )
    file_id: Optional[str] = Field(
        None,
        description="ID of an uploaded file if applicable.",
    )


class TaskResponse(BaseModel):
    task_id: str
    status: str
    created_at: datetime
    result: Optional[str] = None
    artifacts: Optional[list] = None


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
    )
    session_id: Optional[str] = None
    file_path: Optional[str] = None
    has_image: bool = False
    image_path: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    model_used: str
    external_calls: int = 0


# ==========================================================
# MODEL CATALOG
# ==========================================================


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

    return {
        "count": len(models),
        "models": models,
    }


@router.get("/route")
def route_model(
    task: str = Query(
        ...,
        min_length=1,
    ),
    has_image: bool = False,
):
    """Return the local model-router decision."""

    try:
        decision = ModelRouter().route(
            task=task,
            has_image=has_image,
        )

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

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc