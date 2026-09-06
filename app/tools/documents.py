from typing import Any, Dict

from app.multimodal.document_pipeline import DocumentPipeline


class DocumentTool:
    """
    Agent-facing tool for local document extraction.

    Supports PDF, DOCX, and TXT files through the existing
    DocumentPipeline.
    """

    name = "documents"

    def __init__(
        self,
        pipeline: DocumentPipeline | None = None,
    ):
        self.pipeline = (
            pipeline
            or DocumentPipeline()
        )

    def execute(
        self,
        file_path: str,
    ) -> Dict[str, Any]:
        """
        Extract text and metadata from a local document.

        The underlying DocumentPipeline performs PDF extraction
        and OCR when required.
        """

        if not file_path or not file_path.strip():
            raise ValueError(
                "file_path is required."
            )

        result = self.pipeline.extract(
            file_path
        )

        return {
            "status": "processed",
            "source": result.source,
            "file_type": result.file_type,
            "page_count": result.page_count,
            "text": result.text,
            "requires_ocr": result.requires_ocr,
            "ocr_used": result.ocr_used,
            "rendered_pages": result.rendered_pages,
            "page_texts": result.page_texts,
        }