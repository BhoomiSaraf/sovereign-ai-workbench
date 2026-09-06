import pytest

from app.rag.chunker import chunk_text
from app.rag.ingest import KnowledgeIngester
from app.rag.retriever import KnowledgeRetriever


class FakeEmbeddingModel:
    """
    Deterministic fake embedding model for unit tests.

    These tests verify our RAG plumbing without loading
    the real BGE-M3 model.
    """

    def embed_documents(self, texts):
        return [
            [float(len(text)), 1.0]
            for text in texts
        ]

    def embed_query(self, text):
        return [float(len(text)), 1.0]


class FakeStore:
    def __init__(self):
        self.documents = []
        self.embeddings = []
        self.metadatas = []
        self.ids = []

    def add_documents(
        self,
        documents,
        embeddings,
        metadatas,
        ids,
    ):
        self.documents.extend(documents)
        self.embeddings.extend(embeddings)
        self.metadatas.extend(metadatas)
        self.ids.extend(ids)

    def search(
        self,
        embedding,
        top_k,
    ):
        count = min(
            top_k,
            len(self.documents),
        )

        return {
            "documents": [
                self.documents[:count]
            ],
            "metadatas": [
                self.metadatas[:count]
            ],
            "distances": [
                [0.1] * count
            ],
        }


def test_chunk_text_creates_chunks():
    text = "A" * 1000

    chunks = chunk_text(
        text,
        chunk_size=300,
        chunk_overlap=50,
    )

    assert len(chunks) > 1
    assert all(chunks)


def test_chunk_text_rejects_invalid_overlap():
    with pytest.raises(ValueError):
        chunk_text(
            "test",
            chunk_size=100,
            chunk_overlap=100,
        )


def test_ingest_text_stores_source_metadata():
    store = FakeStore()

    ingester = KnowledgeIngester(
        embedding_model=FakeEmbeddingModel(),
        store=store,
    )

    count = ingester.ingest_text(
        text=(
            "Inspection report finding. "
            "Pump vibration exceeded limits."
        ),
        source="inspection_report.pdf",
    )

    assert count > 0
    assert len(store.documents) == count
    assert all(
        metadata["source"]
        == "inspection_report.pdf"
        for metadata in store.metadatas
    )


def test_retriever_returns_source():
    store = FakeStore()

    ingester = KnowledgeIngester(
        embedding_model=FakeEmbeddingModel(),
        store=store,
    )

    ingester.ingest_text(
        text="The pump requires inspection.",
        source="pump_report.pdf",
    )

    retriever = KnowledgeRetriever(
        embedding_model=FakeEmbeddingModel(),
        store=store,
    )

    results = retriever.search(
        "pump inspection",
        top_k=3,
    )

    assert results
    assert results[0].source == "pump_report.pdf"
    assert results[0].text