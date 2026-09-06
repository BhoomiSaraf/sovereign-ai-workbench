from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

import pymupdf
from docx import Document
from pypdf import PdfReader

from app.tools.ocr import OCRTool


@dataclass
class DocumentExtractionResult:
    """
    Result produced by the document extraction pipeline.
    """

    text: str
    source: str
    file_type: str
    page_count: int = 0
    requires_ocr: bool = False
    ocr_used: bool = False


class DocumentPipeline:
    """
    Local document extraction pipeline.

    Supported:
        - PDF
        - DOCX
        - TXT

    PDFs containing little or no extractable text are
    automatically processed through local OCR.
    """

    SUPPORTED_EXTENSIONS = {
        ".pdf",
        ".docx",
        ".txt",
    }

    def __init__(
        self,
        ocr_tool: OCRTool | None = None,
    ):
        self.ocr_tool = (
            ocr_tool
            or OCRTool()
        )

    def extract(
        self,
        file_path: str,
    ) -> DocumentExtractionResult:

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"File not found: {file_path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Path is not a file: {file_path}"
            )

        extension = path.suffix.lower()

        if extension not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported document type: {extension}"
            )

        if extension == ".pdf":
            return self._extract_pdf(path)

        if extension == ".docx":
            return self._extract_docx(path)

        return self._extract_txt(path)

    def _extract_pdf(
        self,
        path: Path,
    ) -> DocumentExtractionResult:

        reader = PdfReader(str(path))

        pages = []

        for page in reader.pages:
            page_text = page.extract_text() or ""

            pages.append(
                page_text.strip()
            )

        text = "\n\n".join(
            page
            for page in pages
            if page
        ).strip()

        requires_ocr = (
            len(text) < 50
            and len(reader.pages) > 0
        )

        ocr_used = False

        if requires_ocr:
            text = self._ocr_pdf(path)
            ocr_used = True

        return DocumentExtractionResult(
            text=text,
            source=path.name,
            file_type="pdf",
            page_count=len(reader.pages),
            requires_ocr=requires_ocr,
            ocr_used=ocr_used,
        )

    def _ocr_pdf(
        self,
        path: Path,
    ) -> str:

        pdf = pymupdf.open(
            str(path)
        )

        page_texts = []

        try:
            with TemporaryDirectory() as temp_dir:

                temp_path = Path(temp_dir)

                for index, page in enumerate(
                    pdf,
                    start=1,
                ):
                    matrix = pymupdf.Matrix(
                        2.0,
                        2.0,
                    )

                    pixmap = page.get_pixmap(
                        matrix=matrix,
                        alpha=False,
                    )

                    image_path = (
                        temp_path
                        / f"page_{index}.png"
                    )

                    pixmap.save(
                        str(image_path)
                    )

                    text = (
                        self.ocr_tool.extract_text(
                            str(image_path)
                        )
                    )

                    if text:
                        page_texts.append(
                            f"Page {index}\n{text}"
                        )

        finally:
            pdf.close()

        return "\n\n".join(
            page_texts
        ).strip()

    def _extract_docx(
        self,
        path: Path,
    ) -> DocumentExtractionResult:

        document = Document(str(path))

        paragraphs = [
            paragraph.text.strip()
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        ]

        text = "\n\n".join(
            paragraphs
        ).strip()

        return DocumentExtractionResult(
            text=text,
            source=path.name,
            file_type="docx",
            page_count=0,
            requires_ocr=False,
            ocr_used=False,
        )

    def _extract_txt(
        self,
        path: Path,
    ) -> DocumentExtractionResult:

        text = path.read_text(
            encoding="utf-8"
        ).strip()

        return DocumentExtractionResult(
            text=text,
            source=path.name,
            file_type="txt",
            page_count=0,
            requires_ocr=False,
            ocr_used=False,
        )


_document_pipeline = DocumentPipeline()


def extract_document(
    file_path: str,
) -> DocumentExtractionResult:

    return _document_pipeline.extract(
        file_path
    )