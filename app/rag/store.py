from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import chromadb


class ChromaStore:
    """
    Local persistent vector store backed by ChromaDB.
    """

    def __init__(
        self,
        persist_directory: str = "data/vector_db",
        collection_name: str = "knowledge",
    ):
        self.persist_directory = Path(
            persist_directory
        )

        self.persist_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory)
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={
                "description": (
                    "Local sovereign AI knowledge base"
                )
            },
        )

    def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
    ) -> None:
        """
        Add embedded document chunks to Chroma.
        """

        if not documents:
            return

        if not (
            len(documents)
            == len(embeddings)
            == len(metadatas)
            == len(ids)
        ):
            raise ValueError(
                "Documents, embeddings, metadata, and IDs "
                "must have the same length."
            )

        self.collection.upsert(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )

    def search(
        self,
        embedding: List[float],
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Search for the most relevant chunks.
        """

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than 0."
            )

        return self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
        )

    def similarity_search_with_score(
        self,
        embedding: List[float],
        top_k: int = 5,
    ) -> List[Tuple[str, Dict[str, Any], float]]:
        """
        Local ChromaDB analogue of similarity_search_with_score.

        Returns (document, metadata, l2_distance) tuples.
        Lower distance is a stronger match.
        """

        results = self.search(
            embedding=embedding,
            top_k=top_k,
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        scored: List[Tuple[str, Dict[str, Any], float]] = []

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

            scored.append(
                (
                    document,
                    metadata or {},
                    float(distance),
                )
            )

        return scored

    def count(self) -> int:
        """Return the number of stored chunks."""

        return self.collection.count()