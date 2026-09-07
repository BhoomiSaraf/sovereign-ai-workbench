from dataclasses import dataclass
from typing import Any, Dict, List, Sequence

from app.rag.embeddings import EmbeddingModel
from app.rag.store import ChromaStore


NO_RELEVANT_INFORMATION = (
    "No sufficiently relevant organizational information found."
)

# ChromaDB default space is L2. Lower distance is a better match.
# A top-1 distance above this threshold is treated as a weak hit.
CONFIDENCE_THRESHOLD = 1.0


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
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
    ):
        self.embedding_model = (
            embedding_model
            or EmbeddingModel()
        )

        self.store = (
            store
            or ChromaStore()
        )

        self.confidence_threshold = confidence_threshold

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[RetrievalResult]:
        """
        Search the local knowledge base using similarity scores.

        If the top result's L2 distance exceeds the confidence
        threshold, a single sentinel result is returned whose
        text is exactly NO_RELEVANT_INFORMATION.
        """

        if not query or not query.strip():
            raise ValueError(
                "Query cannot be empty."
            )

        try:
            query_embedding = (
                self.embedding_model.embed_query(
                    query
                )
            )

            scored = self.store.similarity_search_with_score(
                embedding=query_embedding,
                top_k=top_k,
            )
        except Exception:
            return [
                self._sentinel_result()
            ]

        if not scored:
            return [
                self._sentinel_result()
            ]

        top_distance = float(scored[0][2])

        if top_distance > self.confidence_threshold:
            return [
                self._sentinel_result(score=top_distance)
            ]

        retrieved: List[RetrievalResult] = []

        for document, metadata, distance in scored:
            if float(distance) > self.confidence_threshold:
                continue

            metadata = metadata or {}

            retrieved.append(
                RetrievalResult(
                    text=document,
                    source=str(
                        metadata.get("source", "unknown")
                    ),
                    score=float(distance),
                    metadata=metadata,
                )
            )

        if not retrieved:
            return [
                self._sentinel_result(score=top_distance)
            ]

        return retrieved

    def search_formatted(
        self,
        query: str,
        top_k: int = 5,
    ) -> str:
        """
        Search and return a single citation-formatted string
        suitable for passing to an LLM.
        """

        results = self.search(
            query=query,
            top_k=top_k,
        )

        if self._is_sentinel(results):
            return NO_RELEVANT_INFORMATION

        return self.format_citations(results)

    def format_citations(
        self,
        results: Sequence[RetrievalResult],
    ) -> str:
        """
        Format retrieval results with source, section, and score.
        """

        if self._is_sentinel(results):
            return NO_RELEVANT_INFORMATION

        return "\n\n".join(
            self.format_citation(result)
            for result in results
        )

    def format_citation(
        self,
        result: RetrievalResult,
    ) -> str:
        if result.text == NO_RELEVANT_INFORMATION:
            return NO_RELEVANT_INFORMATION

        metadata = result.metadata or {}

        source = metadata.get("source") or result.source or "unknown"
        section = (
            metadata.get("Header 1")
            or metadata.get("section")
            or "General"
        )

        return (
            f"Source: {source} | Section: {section} "
            f"| Score: {result.score:.4f}\n"
            f"Content: {result.text}"
        )

    def _is_sentinel(
        self,
        results: Sequence[RetrievalResult],
    ) -> bool:
        return (
            len(results) == 1
            and results[0].text == NO_RELEVANT_INFORMATION
        )

    def _sentinel_result(
        self,
        score: float = 0.0,
    ) -> RetrievalResult:
        return RetrievalResult(
            text=NO_RELEVANT_INFORMATION,
            source="",
            score=score,
            metadata={},
        )
