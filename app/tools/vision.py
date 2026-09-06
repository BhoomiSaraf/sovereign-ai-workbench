from typing import Optional

from app.models.manager import ModelManager
from app.multimodal.vision import VisionAnalyzer


class VisionTool:
    """
    Agent-accessible local vision tool.

    The tool performs image analysis using the local
    Qwen2.5-VL model.
    """

    name = "vision"

    def __init__(
        self,
        model_manager: Optional[ModelManager] = None,
    ):
        self.analyzer = VisionAnalyzer(
            model_manager=model_manager
        )

    def execute(
        self,
        image_path: str,
        prompt: str,
    ) -> str:

        return self.analyzer.analyze(
            image_path=image_path,
            prompt=prompt,
        )