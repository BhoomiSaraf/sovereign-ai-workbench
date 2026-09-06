from pathlib import Path
from typing import Optional

from app.models.manager import ModelManager
from app.router.model_registry import get_model_by_name


class VisionAnalyzer:
    """
    Local multimodal image analyzer.

    Uses the registered Qwen2.5-VL model through ModelManager.
    """

    MODEL_NAME = "qwen2.5-vl-3b"

    def __init__(
        self,
        model_manager: Optional[ModelManager] = None,
    ):
        self.model_manager = (
            model_manager or ModelManager()
        )

        self.model = get_model_by_name(
            self.MODEL_NAME
        )

    def analyze(
        self,
        image_path: str,
        prompt: str,
    ) -> str:

        path = Path(image_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Image file not found: {image_path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Image path is not a file: {image_path}"
            )

        if not prompt or not prompt.strip():
            raise ValueError(
                "Vision prompt cannot be empty."
            )

        image_bytes = path.read_bytes()

        if not image_bytes:
            raise ValueError(
                f"Image file is empty: {image_path}"
            )

        return self.model_manager.generate_multimodal(
            model=self.model,
            prompt=prompt,
            images=[image_bytes],
        )


_vision_analyzer = VisionAnalyzer()


def analyze_image(
    image_path: str,
    prompt: str,
) -> str:

    return _vision_analyzer.analyze(
        image_path=image_path,
        prompt=prompt,
    )