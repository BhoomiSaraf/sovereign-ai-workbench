from __future__ import annotations

from pathlib import Path
from typing import Any

import pymupdf


class PDFTool:
    name = "pdf"

    def extract_text(self, file_path: str) -> str:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(file_path)

        if path.suffix.lower() != ".pdf":
            raise ValueError("PDFTool requires a .pdf file.")

        document = pymupdf.open(str(path))

        try:
            pages = []

            for page in document:
                pages.append(page.get_text())

            return "\n\n".join(pages).strip()

        finally:
            document.close()

    def page_count(self, file_path: str) -> int:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(file_path)

        document = pymupdf.open(str(path))

        try:
            return len(document)
        finally:
            document.close()

    def metadata(self, file_path: str) -> dict[str, Any]:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(file_path)

        document = pymupdf.open(str(path))

        try:
            return {
                "page_count": len(document),
                "metadata": document.metadata,
            }
        finally:
            document.close()