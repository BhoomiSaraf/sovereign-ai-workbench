from typing import List, Optional

import ollama

from app.models.base import BaseModelProvider


class OllamaProvider(BaseModelProvider):
    """
    Local Ollama model provider.

    All inference happens through the local Ollama service.
    """

    def __init__(
        self,
        host: str = "http://localhost:11434",
    ):
        self.host = host
        self.client = ollama.Client(host=host)

    # --------------------------------------------------
    # Text generation
    # --------------------------------------------------

    def generate(
        self,
        model_name: str,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> str:

        messages = []

        if system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        response = self.client.chat(
            model=model_name,
            messages=messages,
        )

        return response["message"]["content"]

    # --------------------------------------------------
    # Multimodal generation
    # --------------------------------------------------

    def generate_multimodal(
        self,
        model_name: str,
        prompt: str,
        images: List[bytes],
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate a response from text and local image bytes.

        Images are passed directly to Ollama.
        No external service is contacted.
        """

        if not images:
            raise ValueError(
                "At least one image is required."
            )

        messages = []

        if system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt,
                "images": images,
            }
        )

        response = self.client.chat(
            model=model_name,
            messages=messages,
        )

        return response["message"]["content"]

    # --------------------------------------------------
    # Availability
    # --------------------------------------------------

    def is_available(self) -> bool:

        try:
            self.client.list()
            return True

        except Exception:
            return False

    # --------------------------------------------------
    # Installed models
    # --------------------------------------------------

    def list_models(self):

        response = self.client.list()

        return response.get(
            "models",
            [],
        )