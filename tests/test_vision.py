from pathlib import Path

import pytest

from app.multimodal.vision import VisionAnalyzer


class FakeVisionManager:

    def __init__(self):
        self.calls = []

    def generate_multimodal(
        self,
        model,
        prompt,
        images,
        system_prompt=None,
    ):
        self.calls.append(
            {
                "model": model,
                "prompt": prompt,
                "images": images,
                "system_prompt": system_prompt,
            }
        )

        return "Detected pump P-101 and connected piping."


def test_vision_analyzer_passes_local_image_to_model(
    tmp_path: Path,
):
    image_path = tmp_path / "diagram.png"

    image_bytes = b"fake-image-data"

    image_path.write_bytes(image_bytes)

    manager = FakeVisionManager()

    analyzer = VisionAnalyzer(
        model_manager=manager
    )

    result = analyzer.analyze(
        image_path=str(image_path),
        prompt="Describe the equipment and connections.",
    )

    assert result == (
        "Detected pump P-101 and connected piping."
    )

    assert len(manager.calls) == 1

    call = manager.calls[0]

    assert call["images"] == [image_bytes]

    assert (
        call["prompt"]
        == "Describe the equipment and connections."
    )

    assert call["model"].name == "qwen2.5-vl-3b"


def test_vision_analyzer_missing_image():

    manager = FakeVisionManager()

    analyzer = VisionAnalyzer(
        model_manager=manager
    )

    with pytest.raises(FileNotFoundError):

        analyzer.analyze(
            image_path="does_not_exist.png",
            prompt="Analyze this image.",
        )


def test_vision_analyzer_rejects_empty_prompt(
    tmp_path: Path,
):
    image_path = tmp_path / "image.png"

    image_path.write_bytes(
        b"fake-image-data"
    )

    manager = FakeVisionManager()

    analyzer = VisionAnalyzer(
        model_manager=manager
    )

    with pytest.raises(ValueError):

        analyzer.analyze(
            image_path=str(image_path),
            prompt="",
        )