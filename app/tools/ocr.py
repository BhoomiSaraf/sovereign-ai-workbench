from pathlib import Path
from typing import List

import pytesseract
from PIL import Image


class OCRTool:
    """
    Local OCR tool backed by Tesseract.

    Tesseract is expected to be installed locally and
    available through the system PATH.
    """

    def __init__(
        self,
        tesseract_cmd: str | None = None,
    ):
        if tesseract_cmd:
            path = Path(tesseract_cmd)

            if not path.exists():
                raise FileNotFoundError(
                    f"Tesseract executable not found: {tesseract_cmd}"
                )

            pytesseract.pytesseract.tesseract_cmd = (
                str(path)
            )

        else:
            # Use the normal Tesseract executable
            # discovered through the system PATH.
            pytesseract.pytesseract.tesseract_cmd = (
                "tesseract"
            )

        self._verify_tesseract()

    def _verify_tesseract(self) -> None:
        """
        Verify that the configured Tesseract executable
        is actually available.
        """

        try:
            pytesseract.get_tesseract_version()

        except Exception as exc:
            raise RuntimeError(
                "Tesseract OCR is not available. "
                "Install Tesseract and ensure its executable "
                "is available on the system PATH."
            ) from exc

    def extract_text(
        self,
        image_path: str,
    ) -> str:
        """
        Extract text from a local image.
        """

        path = Path(image_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Image not found: {image_path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Path is not a file: {image_path}"
            )

        try:
            with Image.open(path) as image:
                text = pytesseract.image_to_string(
                    image
                )

        except Exception as exc:
            raise RuntimeError(
                f"OCR failed for '{path.name}': {exc}"
            ) from exc

        return text.strip()

    def extract_images(
        self,
        image_paths: List[str],
    ) -> str:
        """
        Extract and combine OCR text from multiple images.
        """

        pages = []

        for index, image_path in enumerate(
            image_paths,
            start=1,
        ):
            text = self.extract_text(
                image_path
            )

            if text:
                pages.append(
                    f"Page {index}\n{text}"
                )

        return "\n\n".join(pages)


_ocr_tool = OCRTool()


def extract_text_from_image(
    image_path: str,
) -> str:
    """
    Convenience function for application code.
    """

    return _ocr_tool.extract_text(
        image_path
    )