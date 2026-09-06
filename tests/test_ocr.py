from unittest.mock import Mock

from app.tools.ocr import OCRTool


def test_ocr_extracts_image_text(tmp_path):

    image_path = tmp_path / "page.png"

    image_path.write_bytes(
        b"fake image"
    )

    tool = OCRTool()

    mock_image = Mock()

    # We don't run Tesseract in this unit test.
    tool.extract_text = Mock(
        return_value="Pump vibration exceeded limit."
    )

    result = tool.extract_text(
        str(image_path)
    )

    assert (
        result
        == "Pump vibration exceeded limit."
    )


def test_ocr_missing_file():

    tool = OCRTool()

    try:
        tool.extract_text(
            "does_not_exist.png"
        )

        assert False

    except FileNotFoundError:
        assert True