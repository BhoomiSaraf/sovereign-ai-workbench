from pathlib import Path

import pytest
from docx import Document

from app.multimodal.document_pipeline import (
    DocumentPipeline,
)


def test_txt_extraction(tmp_path):

    file_path = tmp_path / "report.txt"

    file_path.write_text(
        "Pump vibration exceeded the allowed limit.",
        encoding="utf-8",
    )

    result = DocumentPipeline().extract(
        str(file_path)
    )

    assert (
        result.text
        == "Pump vibration exceeded the allowed limit."
    )

    assert result.file_type == "txt"
    assert result.requires_ocr is False


def test_docx_extraction(tmp_path):

    file_path = tmp_path / "report.docx"

    document = Document()

    document.add_paragraph(
        "Inspection finding: excessive vibration."
    )

    document.save(file_path)

    result = DocumentPipeline().extract(
        str(file_path)
    )

    assert (
        "excessive vibration"
        in result.text
    )

    assert result.file_type == "docx"
    assert result.requires_ocr is False


def test_unsupported_document_type(
    tmp_path,
):

    file_path = tmp_path / "report.xyz"

    file_path.write_text(
        "test",
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        DocumentPipeline().extract(
            str(file_path)
        )