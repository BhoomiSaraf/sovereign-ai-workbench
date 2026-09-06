from abc import ABC, abstractmethod
from typing import List, Optional


class BaseModelProvider(ABC):

    @abstractmethod
    def generate(
        self,
        model_name: str,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        raise NotImplementedError

    def generate_multimodal(
        self,
        model_name: str,
        prompt: str,
        images: List[bytes],
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate a response using text plus one or more images.

        Providers that support multimodal models should override this.
        """

        raise NotImplementedError(
            f"Provider does not support multimodal generation "
            f"for model '{model_name}'."
        )

    @abstractmethod
    def is_available(self) -> bool:
        raise NotImplementedError