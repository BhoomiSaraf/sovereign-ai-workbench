from dataclasses import dataclass, field
from pathlib import Path

import pymupdf
from docx import Document
from pypdf import PdfReader

from app.tools.ocr import OCRTool


@dataclass
class DocumentExtractionResult:
    """
    Result of local document extraction.

    For OCR PDFs, page_texts and rendered_pages are kept
    explicitly page-aligned:

        page_texts[0] <-> rendered_pages[0]
        page_texts[1] <-> rendered_pages[1]
        ...

    This prevents OCR-detected page numbers, headers, or
    footers from corrupting page alignment.
    """

    text: str
    source: str
    file_type: str
    page_count: int = 0
    requires_ocr: bool = False
    ocr_used: bool = False

    rendered_pages: list[str] = field(
        default_factory=list
    )

    page_texts: list[str] = field(
        default_factory=list
    )


class DocumentPipeline:

    SUPPORTED_EXTENSIONS = {
        ".pdf",
        ".docx",
        ".txt",
        ".md",
        ".markdown",
    }

    def __init__(
        self,
        ocr_tool=None,
    ):
        self.ocr_tool = (
            ocr_tool or OCRTool()
        )

    # ==========================================================
    # PUBLIC API
    # ==========================================================

    def extract(
        self,
        file_path: str,
    ) -> DocumentExtractionResult:

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Document not found: {file_path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Expected a file: {file_path}"
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

        file_type = (
            "md"
            if extension in {".md", ".markdown"}
            else "txt"
        )

        return self._extract_txt(path, file_type=file_type)

    # ==========================================================
    # PDF
    # ==========================================================

    def _extract_pdf(
        self,
        file_path: Path,
    ) -> DocumentExtractionResult:

        reader = PdfReader(
            str(file_path)
        )

        page_texts = []

        for page in reader.pages:

            try:
                text = (
                    page.extract_text()
                    or ""
                )
            except Exception:
                text = ""

            page_texts.append(
                text.strip()
            )

        text = "\n\n".join(
            page_texts
        ).strip()

        page_count = len(
            reader.pages
        )

        # Preserve the previous OCR detection
        # behavior.
        requires_ocr = (
            len(text) < 50
            and page_count > 0
        )

        if requires_ocr:

            (
                ocr_text,
                rendered_pages,
                ocr_page_texts,
            ) = self._ocr_pdf(
                file_path
            )

            return DocumentExtractionResult(
                text=ocr_text,
                source=str(file_path),
                file_type="pdf",
                page_count=page_count,
                requires_ocr=True,
                ocr_used=True,
                rendered_pages=rendered_pages,
                page_texts=ocr_page_texts,
            )

        return DocumentExtractionResult(
            text=text,
            source=str(file_path),
            file_type="pdf",
            page_count=page_count,
            requires_ocr=False,
            ocr_used=False,
            rendered_pages=[],
            page_texts=page_texts,
        )

    # ==========================================================
    # OCR PDF
    # ==========================================================

    def _ocr_pdf(
        self,
        file_path: Path,
    ):
        """
        Render every PDF page and OCR each rendered image.

        OCRTool.extract_text() is used because that is the
        existing OCRTool public API.

        The OCR result for each page is stored directly in
        page_texts at the same index as its rendered image.
        """

        rendered_pages = []
        page_texts = []

        output_dir = (
            Path("data")
            / "executions"
            / "rendered_pages"
            / file_path.stem
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        pdf = pymupdf.open(
            str(file_path)
        )

        try:

            for index, page in enumerate(
                pdf,
                start=1,
            ):

                pixmap = page.get_pixmap(
                    matrix=pymupdf.Matrix(
                        2,
                        2,
                    ),
                    alpha=False,
                )

                image_path = (
                    output_dir
                    / f"page_{index:03d}.png"
                )

                pixmap.save(
                    str(image_path)
                )

                rendered_pages.append(
                    str(image_path)
                )

                # IMPORTANT:
                # Use the existing OCRTool API.
                page_text = (
                    self.ocr_tool.extract_text(
                        str(image_path)
                    )
                    or ""
                )

                page_texts.append(
                    page_text.strip()
                )

        finally:
            pdf.close()

        # Human-readable combined document text.
        #
        # Page markers are useful here, but downstream
        # page-aware processing uses page_texts directly.
        text = "\n\n".join(
            f"Page {index}\n{page_text}"
            for index, page_text in enumerate(
                page_texts,
                start=1,
            )
        )

        return (
            text,
            rendered_pages,
            page_texts,
        )

    # ==========================================================
    # DOCX
    # ==========================================================

    def _extract_docx(
        self,
        file_path: Path,
    ) -> DocumentExtractionResult:

        document = Document(
            str(file_path)
        )

        paragraphs = [
            paragraph.text
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        ]

        text = "\n".join(
            paragraphs
        ).strip()

        return DocumentExtractionResult(
            text=text,
            source=str(file_path),
            file_type="docx",
            page_count=0,
            requires_ocr=False,
            ocr_used=False,
            rendered_pages=[],
            page_texts=[],
        )

    # ==========================================================
    # TXT
    # ==========================================================

    def _extract_txt(
        self,
        file_path: Path,
        file_type: str = "txt",
    ) -> DocumentExtractionResult:

        text = file_path.read_text(
            encoding="utf-8",
            errors="replace",
        ).strip()

        return DocumentExtractionResult(
            text=text,
            source=str(file_path),
            file_type=file_type,
            page_count=0,
            requires_ocr=False,
            ocr_used=False,
            rendered_pages=[],
            page_texts=[],
        )