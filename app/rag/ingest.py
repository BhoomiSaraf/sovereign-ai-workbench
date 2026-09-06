from pathlib import Path
from typing import Any, Dict

from app.multimodal.document_pipeline import (
    DocumentPipeline,
)
from app.rag.chunker import chunk_text
from app.rag.embeddings import EmbeddingModel
from app.rag.store import ChromaStore


class KnowledgeIngester:
    """
    Converts local documents into searchable knowledge.

    Pipeline:

        document
            ↓
        extraction / OCR
            ↓
        chunks
            ↓
        BGE-M3 embeddings
            ↓
        ChromaDB
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

    def ingest_text(
        self,
        text: str,
        source: str,
        metadata: Dict[str, Any] | None = None,
    ) -> int:

        if not text or not text.strip():
            raise ValueError(
                "Cannot ingest empty text."
            )

        if not source or not source.strip():
            raise ValueError(
                "Source is required."
            )

        chunks = chunk_text(text)

        if not chunks:
            return 0

        embeddings = (
            self.embedding_model.embed_documents(
                chunks
            )
        )

        base_metadata = dict(
            metadata or {}
        )

        base_metadata["source"] = source

        metadatas = []

        for index in range(len(chunks)):

            chunk_metadata = dict(
                base_metadata
            )

            chunk_metadata["chunk_index"] = (
                index
            )

            metadatas.append(
                chunk_metadata
            )

        source_stem = Path(
            source
        ).stem

        ids = [
            f"{source_stem}-{index}"
            for index in range(len(chunks))
        ]

        self.store.add_documents(
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )

        return len(chunks)

    def ingest_file(
        self,
        file_path: str,
        metadata: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:

        result = (
            self.document_pipeline.extract(
                file_path
            )
        )

        chunks = self.ingest_text(
            text=result.text,
            source=result.source,
            metadata={
                **(metadata or {}),
                "file_type": result.file_type,
                "page_count": result.page_count,
                "ocr_used": result.ocr_used,
            },
        )

        return {
            "status": "ingested",
            "source": result.source,
            "file_type": result.file_type,
            "page_count": result.page_count,
            "chunks": chunks,
            "ocr_used": result.ocr_used,
        }