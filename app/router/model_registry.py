from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class ModelConfig:
    """
    Describes a locally available AI model.

    capabilities:
        Capability strength from 0 to 5.
        0 = unsupported
        1 = poor
        2 = limited
        3 = acceptable
        4 = strong
        5 = excellent

    modalities:
        Input types supported by the model.
        Examples: "text", "image"

    priority:
        Tie-breaker only.
        Lower number = preferred when models have
        essentially the same capability score.
    """

    name: str
    ollama_name: str
    capabilities: Dict[str, int]
    modalities: List[str]
    priority: int


MODEL_REGISTRY = [
    ModelConfig(
        name="qwen3-4b",
        ollama_name="qwen3:4b",
        capabilities={
            "reasoning": 4,
            "planning": 4,
            "summarization": 5,
            "general": 5,
            "tool_calling": 4,
            "document_analysis": 4,
            "coding": 2,
            "debugging": 2,
        },
        modalities=[
            "text",
        ],
        priority=1,
    ),

    ModelConfig(
        name="qwen2.5-coder-7b",
        ollama_name="qwen2.5-coder:7b",
        capabilities={
            "coding": 5,
            "debugging": 5,
            "code_review": 5,
            "programming": 5,
            "reasoning": 4,
            "general": 3,
            "summarization": 3,
        },
        modalities=[
            "text",
        ],
        priority=2,
    ),

    ModelConfig(
        name="qwen2.5-vl-3b",
        ollama_name="qwen2.5vl:3b",
        capabilities={
            "vision": 5,
            "document_vision": 5,
            "image_analysis": 5,
            "diagram_analysis": 5,
            "ocr_reasoning": 4,
            "reasoning": 3,
            "document_analysis": 4,
        },
        modalities=[
            "text",
            "image",
        ],
        priority=2,
    ),
]


def get_available_models() -> List[ModelConfig]:
    """Return all registered local models."""
    return MODEL_REGISTRY.copy()


def get_model_by_name(model_name: str) -> ModelConfig:
    """Return a registered model by its internal name."""

    for model in MODEL_REGISTRY:
        if model.name == model_name:
            return model

    raise ValueError(
        f"Model '{model_name}' is not registered."
    )