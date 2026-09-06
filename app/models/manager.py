from typing import List, Optional

from app.models.base import BaseModelProvider
from app.models.ollama import OllamaProvider
from app.router.model_registry import ModelConfig


class ModelManager:
    """
    Central model lifecycle and inference manager.

    The manager keeps the rest of the application independent
    from the underlying inference provider.
    """

    def __init__(
        self,
        provider: Optional[BaseModelProvider] = None,
    ):
        self.provider = provider or OllamaProvider()

    # --------------------------------------------------
    # Text generation
    # --------------------------------------------------

    def generate(
        self,
        model: ModelConfig,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> str:

        return self.provider.generate(
            model_name=model.ollama_name,
            prompt=prompt,
            system_prompt=system_prompt,
        )

    # --------------------------------------------------
    # Multimodal generation
    # --------------------------------------------------

    def generate_multimodal(
        self,
        model: ModelConfig,
        prompt: str,
        images: List[bytes],
        system_prompt: Optional[str] = None,
    ) -> str:

        return self.provider.generate_multimodal(
            model_name=model.ollama_name,
            prompt=prompt,
            images=images,
            system_prompt=system_prompt,
        )

    # --------------------------------------------------
    # Provider availability
    # --------------------------------------------------

    def is_available(self) -> bool:

        return self.provider.is_available()

    # --------------------------------------------------
    # Installed models
    # --------------------------------------------------

    def list_installed_models(self):

        if not hasattr(
            self.provider,
            "list_models",
        ):
            return []

        return self.provider.list_models()