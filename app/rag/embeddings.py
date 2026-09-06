from typing import List, Optional

from sentence_transformers import SentenceTransformer


class EmbeddingModel:
    """
    Local embedding model wrapper.

    Default model:
        BAAI/bge-m3

    The model is loaded locally and used only for embedding
    documents and queries.
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
    ):
        self.model_name = model_name
        self._model: Optional[SentenceTransformer] = None

    @property
    def model(self) -> SentenceTransformer:
        """
        Lazily load the embedding model.

        This prevents model loading during application
        startup when embeddings are not needed yet.
        """

        if self._model is None:
            self._model = SentenceTransformer(
                self.model_name
            )

        return self._model

    def embed_documents(
        self,
        texts: List[str],
    ) -> List[List[float]]:
        """
        Generate embeddings for document chunks.
        """

        if not texts:
            return []

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return embeddings.tolist()

    def embed_query(
        self,
        text: str,
    ) -> List[float]:
        """
        Generate an embedding for a search query.
        """

        if not text or not text.strip():
            raise ValueError(
                "Query cannot be empty."
            )

        embedding = self.model.encode(
            text,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return embedding.tolist()