from dataclasses import dataclass
from typing import Any, Dict, List

from app.rag.embeddings import EmbeddingModel
from app.rag.store import ChromaStore


@dataclass
class RetrievalResult:
    """
    A single knowledge retrieval result.
    """

    text: str
    source: str
    score: float
    metadata: Dict[str, Any]


class KnowledgeRetriever:
    """
    Retrieves relevant private knowledge from the
    local vector database.
    """

    def __init__(
        self,
        embedding_model: EmbeddingModel | None = None,
        store: ChromaStore | None = None,
    ):
        self.embedding_model = (
            embedding_model
            or EmbeddingModel()
        )

        self.store = (
            store
            or ChromaStore()
        )

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[RetrievalResult]:
        """
        Search the local knowledge base.
        """

        if not query or not query.strip():
            raise ValueError(
                "Query cannot be empty."
            )

        query_embedding = (
            self.embedding_model.embed_query(
                query
            )
        )

        results = self.store.search(
            embedding=query_embedding,
            top_k=top_k,
        )

        documents = results.get(
            "documents",
            [[]],
        )[0]

        metadatas = results.get(
            "metadatas",
            [[]],
        )[0]

        distances = results.get(
            "distances",
            [[]],
        )[0]

        retrieved = []

        for index, document in enumerate(documents):

            metadata = (
                metadatas[index]
                if index < len(metadatas)
                else {}
            )

            distance = (
                distances[index]
                if index < len(distances)
                else 0.0
            )

            source = str(
                metadata.get(
                    "source",
                    "unknown",
                )
            )

            retrieved.append(
                RetrievalResult(
                    text=document,
                    source=source,
                    score=float(distance),
                    metadata=metadata,
                )
            )

        return retrieved