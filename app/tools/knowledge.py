from typing import Any, Dict, List

from app.rag.retriever import KnowledgeRetriever


class KnowledgeTool:
    """
    Agent-facing tool for searching the private
    organizational knowledge base.
    """

    name = "knowledge_search"

    def __init__(
        self,
        retriever: KnowledgeRetriever | None = None,
    ):
        self.retriever = (
            retriever
            or KnowledgeRetriever()
        )

    def execute(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search the local organizational knowledge base.

        Returns serializable dictionaries suitable for
        AgentState and API responses.
        """

        if not query or not query.strip():
            raise ValueError(
                "Knowledge search query cannot be empty."
            )

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than 0."
            )

        results = self.retriever.search(
            query=query,
            top_k=top_k,
        )

        return [
            {
                "text": result.text,
                "source": result.source,
                "score": result.score,
                "metadata": result.metadata,
            }
            for result in results
        ]