from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from app.multimodal.document_pipeline import (
    DocumentPipeline,
)
from app.rag.embeddings import EmbeddingModel
from app.rag.store import ChromaStore


SUPPORTED_INGEST_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt",
    ".md",
    ".markdown",
}

HEADER_SPLIT_CONFIG = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]

MAX_SECTION_CHARS = 800
SECTION_OVERLAP_CHARS = 120


class KnowledgeIngester:
    """
    Converts local documents into searchable knowledge.

    Pipeline:

        PDF / DOCX / TXT / Markdown
            ↓
        extraction (text treated as Markdown)
            ↓
        heading-aware chunking
            ↓
        recursive fallback for oversized sections
            ↓
        BGE-M3 embeddings
            ↓
        local ChromaDB
    """

    def __init__(
        self,
        embedding_model: EmbeddingModel | None = None,
        store: ChromaStore | None = None,
        document_pipeline: DocumentPipeline | None = None,
    ):
        self.embedding_model = (
            embedding_model
            or EmbeddingModel()
        )

        self.store = (
            store
            or ChromaStore()
        )

        self.document_pipeline = (
            document_pipeline
            or DocumentPipeline()
        )

        self._header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=HEADER_SPLIT_CONFIG,
            strip_headers=False,
        )

        self._fallback_splitter = RecursiveCharacterTextSplitter(
            chunk_size=MAX_SECTION_CHARS,
            chunk_overlap=SECTION_OVERLAP_CHARS,
        )

    def ingest_text(
        self,
        text: str,
        source: str,
        metadata: Dict[str, Any] | None = None,
        document_type: str | None = None,
        date_ingested: str | None = None,
    ) -> int:
        """
        Chunk markdown-formatted text and upsert it into ChromaDB.
        """

        if not text or not text.strip():
            raise ValueError(
                "Cannot ingest empty text."
            )

        if not source or not source.strip():
            raise ValueError(
                "Source is required."
            )

        resolved_type = (
            document_type
            or self._document_type_from_source(source)
        )

        resolved_date = (
            date_ingested
            or datetime.now(timezone.utc).date().isoformat()
        )

        chunks = self._chunk_markdown(
            text=text,
            source=source,
            document_type=resolved_type,
            date_ingested=resolved_date,
            extra_metadata=metadata,
        )

        if not chunks:
            return 0

        documents = [
            chunk["text"]
            for chunk in chunks
        ]

        embeddings = (
            self.embedding_model.embed_documents(
                documents
            )
        )

        metadatas = [
            chunk["metadata"]
            for chunk in chunks
        ]

        source_stem = Path(source).stem

        ids = [
            f"{source_stem}-{index}"
            for index in range(len(documents))
        ]

        self.store.add_documents(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )

        return len(documents)

    def ingest_file(
        self,
        file_path: str,
        metadata: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """
        Extract a local PDF, DOCX, TXT, or Markdown file and ingest it.
        """

        try:
            path = Path(file_path)

            if not path.exists():
                raise FileNotFoundError(
                    f"Document not found: {file_path}"
                )

            extension = path.suffix.lower()

            if extension not in SUPPORTED_INGEST_EXTENSIONS:
                raise ValueError(
                    "Unsupported document type: "
                    f"{extension}. Supported types: "
                    "PDF, DOCX, TXT, Markdown."
                )

            text, extracted_meta = self._extract_as_markdown(
                path
            )

            chunks = self.ingest_text(
                text=text,
                source=path.name,
                document_type=extracted_meta["document_type"],
                metadata={
                    **(metadata or {}),
                    **extracted_meta.get(
                        "pipeline_metadata",
                        {},
                    ),
                },
            )

            return {
                "status": "ingested",
                "source": path.name,
                "document_type": extracted_meta[
                    "document_type"
                ],
                "file_type": extracted_meta[
                    "document_type"
                ],
                "page_count": extracted_meta.get(
                    "page_count",
                    0,
                ),
                "chunks": chunks,
                "ocr_used": extracted_meta.get(
                    "ocr_used",
                    False,
                ),
            }

        except Exception as exc:
            return {
                "status": "error",
                "source": str(file_path),
                "error": str(exc),
                "chunks": 0,
            }

    def _extract_as_markdown(
        self,
        path: Path,
    ) -> Tuple[str, Dict[str, Any]]:
        extension = path.suffix.lower()

        if extension in {".md", ".markdown", ".txt"}:
            text = path.read_text(
                encoding="utf-8",
                errors="replace",
            )

            document_type = (
                "md"
                if extension in {".md", ".markdown"}
                else "txt"
            )

            markdown = self._ensure_markdown(
                text,
                title=path.stem.replace("_", " "),
            )

            return markdown, {
                "document_type": document_type,
                "page_count": 0,
                "ocr_used": False,
                "pipeline_metadata": {},
            }

        result = self.document_pipeline.extract(
            str(path)
        )

        markdown = self._ensure_markdown(
            result.text,
            title=path.stem.replace("_", " "),
        )

        return markdown, {
            "document_type": result.file_type,
            "page_count": result.page_count,
            "ocr_used": result.ocr_used,
            "pipeline_metadata": {
                "file_type": result.file_type,
                "page_count": result.page_count,
                "ocr_used": result.ocr_used,
            },
        }

    def _ensure_markdown(
        self,
        text: str,
        title: str,
    ) -> str:
        stripped = (text or "").strip()

        if not stripped:
            raise ValueError(
                "Cannot ingest empty text."
            )

        if stripped.lstrip().startswith("#"):
            return stripped

        return f"# {title}\n\n{stripped}"

    def _chunk_markdown(
        self,
        text: str,
        source: str,
        document_type: str,
        date_ingested: str,
        extra_metadata: Dict[str, Any] | None,
    ) -> List[Dict[str, Any]]:
        try:
            header_docs = self._header_splitter.split_text(
                text
            )
        except Exception:
            header_docs = []

        if not header_docs:
            header_docs = [
                _PlainDocument(text, {})
            ]

        chunks: List[Dict[str, Any]] = []

        for header_doc in header_docs:
            page_content = getattr(
                header_doc,
                "page_content",
                str(header_doc),
            ).strip()

            if not page_content:
                continue

            header_meta = dict(
                getattr(header_doc, "metadata", {}) or {}
            )

            section = self._section_from_headers(
                header_meta
            )

            if len(page_content) > MAX_SECTION_CHARS:
                sub_texts = self._fallback_splitter.split_text(
                    page_content
                )
            else:
                sub_texts = [page_content]

            for sub_text in sub_texts:
                content = sub_text.strip()

                if not content:
                    continue

                chunk_metadata = self._build_chunk_metadata(
                    source=source,
                    document_type=document_type,
                    date_ingested=date_ingested,
                    section=section,
                    header_meta=header_meta,
                    extra_metadata=extra_metadata,
                    chunk_index=len(chunks),
                )

                chunks.append(
                    {
                        "text": content,
                        "metadata": chunk_metadata,
                    }
                )

        return chunks

    def _build_chunk_metadata(
        self,
        source: str,
        document_type: str,
        date_ingested: str,
        section: str,
        header_meta: Dict[str, Any],
        extra_metadata: Dict[str, Any] | None,
        chunk_index: int,
    ) -> Dict[str, Any]:
        metadata: Dict[str, Any] = {}

        if extra_metadata:
            metadata.update(extra_metadata)

        metadata.update(header_meta)

        metadata["source"] = source
        metadata["document_type"] = document_type
        metadata["date_ingested"] = date_ingested
        metadata["section"] = section
        metadata["chunk_index"] = chunk_index

        return self._chroma_safe_metadata(metadata)

    def _section_from_headers(
        self,
        header_meta: Dict[str, Any],
    ) -> str:
        for key in ("Header 3", "Header 2", "Header 1"):
            value = header_meta.get(key)

            if value:
                return str(value)

        return "General"

    def _document_type_from_source(
        self,
        source: str,
    ) -> str:
        suffix = Path(source).suffix.lower().lstrip(".")

        if suffix in {"markdown"}:
            return "md"

        return suffix or "txt"

    def _chroma_safe_metadata(
        self,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        ChromaDB only accepts str, int, float, or bool metadata values.
        """

        safe: Dict[str, Any] = {}

        for key, value in metadata.items():
            if value is None:
                continue

            if isinstance(value, (str, int, float, bool)):
                safe[str(key)] = value
            else:
                safe[str(key)] = str(value)

        return safe


class _PlainDocument:
    """Minimal stand-in when header splitting yields nothing."""

    def __init__(
        self,
        page_content: str,
        metadata: Dict[str, Any],
    ):
        self.page_content = page_content
        self.metadata = metadata
