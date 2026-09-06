from dataclasses import dataclass
from pathlib import Path
from typing import List

import numpy as np

from app.rag.embeddings import EmbeddingModel


@dataclass
class PageRelevance:
    page_number: int
    image_path: str
    score: float
    text: str


class SemanticPageSelector:
    """
    Selects visually relevant document pages using local embeddings.

    No task-specific keywords or document-specific rules are used.
    """

    def __init__(self, embedding_model=None):
        self.embedding_model = embedding_model or EmbeddingModel()

    def select(
        self,
        query: str,
        pages: List[str],
        page_texts: List[str],
        top_k: int = 1,
    ) -> List[PageRelevance]:

        return self.rank(
            query=query,
            pages=pages,
            page_texts=page_texts,
        )[:max(1, top_k)]

    def rank(
        self,
        query: str,
        pages: List[str],
        page_texts: List[str],
    ) -> List[PageRelevance]:
        """
        Rank all available pages by semantic relevance.
        """

        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        if len(pages) != len(page_texts):
            raise ValueError(
                "pages and page_texts must have the same length."
            )

        valid_pages = []

        for index, (image_path, text) in enumerate(
            zip(pages, page_texts),
            start=1,
        ):
            if not image_path:
                continue

            if not Path(image_path).exists():
                continue

            valid_pages.append(
                (
                    index,
                    image_path,
                    text or "",
                )
            )

        if not valid_pages:
            return []

        query_embedding = np.asarray(
            self.embedding_model.embed_query(query),
            dtype=np.float32,
        )

        texts = [
            text if text.strip() else "[No extracted text]"
            for _, _, text in valid_pages
        ]

        page_embeddings = np.asarray(
            self.embedding_model.embed_documents(texts),
            dtype=np.float32,
        )

        scores = page_embeddings @ query_embedding

        ranked = []

        for item, score in zip(valid_pages, scores):
            page_number, image_path, text = item

            ranked.append(
                PageRelevance(
                    page_number=page_number,
                    image_path=image_path,
                    score=float(score),
                    text=text,
                )
            )

        ranked.sort(
            key=lambda result: result.score,
            reverse=True,
        )

        return ranked