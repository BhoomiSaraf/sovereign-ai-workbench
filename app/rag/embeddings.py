import os
import json
from pathlib import Path
from typing import List, Optional

from sentence_transformers import SentenceTransformer


class EmbeddingModel:
    """
    Local-only embedding model wrapper.

    The model must already exist in the local Hugging Face cache.
    Runtime execution never downloads models or contacts the Hub.
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        local_files_only: bool = True,
    ):
        self.model_name = model_name
        self.local_files_only = local_files_only
        self._model: Optional[SentenceTransformer] = None

        if self.local_files_only:
            os.environ["HF_HUB_OFFLINE"] = "1"
            os.environ["TRANSFORMERS_OFFLINE"] = "1"

    def _find_local_model(self) -> str:
        """
        Locate an already-cached Hugging Face model without contacting
        the Hugging Face Hub.
        """

        cache_root = Path(
            os.environ.get(
                "HF_HOME",
                Path.home() / ".cache" / "huggingface",
            )
        )

        model_dir = (
            cache_root
            / "hub"
            / f"models--{self.model_name.replace('/', '--')}"
        )

        snapshots_dir = model_dir / "snapshots"

        if not snapshots_dir.exists():
            raise FileNotFoundError(
                f"Local embedding model not found: {self.model_name}. "
                f"Expected cache directory: {model_dir}"
            )

        snapshots = [
            path for path in snapshots_dir.iterdir()
            if path.is_dir()
        ]

        usable = [
            path for path in snapshots
            if self._snapshot_is_usable(path)
        ]

        if not usable:
            raise FileNotFoundError(
                f"No complete local snapshot found for {self.model_name} "
                f"inside {snapshots_dir}"
            )

        preferred_ref = model_dir / "refs" / "main"

        if preferred_ref.exists():
            preferred_hash = preferred_ref.read_text(
                encoding="utf-8"
            ).strip()
            preferred = snapshots_dir / preferred_hash

            if preferred in usable:
                return str(preferred)

        snapshot = max(
            usable,
            key=lambda path: path.stat().st_mtime,
        )

        return str(snapshot)

    def _snapshot_is_usable(self, snapshot: Path) -> bool:
        """
        A snapshot is usable only if it has a recognisable
        transformers config and local model weights.
        """

        config_path = snapshot / "config.json"

        if not config_path.exists():
            return False

        try:
            config = json.loads(
                config_path.read_text(encoding="utf-8")
            )
        except Exception:
            return False

        if not config.get("model_type"):
            return False

        weight_names = (
            "pytorch_model.bin",
            "model.safetensors",
            "pytorch_model.bin.index.json",
            "model.safetensors.index.json",
        )

        return any(
            (snapshot / name).exists()
            for name in weight_names
        )

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            if self.local_files_only:
                model_path = self._find_local_model()

                self._model = SentenceTransformer(
                    model_path,
                    local_files_only=True,
                )
            else:
                self._model = SentenceTransformer(
                    self.model_name,
                    local_files_only=False,
                )

        return self._model

    def embed_documents(
        self,
        texts: List[str],
    ) -> List[List[float]]:
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
        if not text or not text.strip():
            raise ValueError("Query cannot be empty.")

        embedding = self.model.encode(
            text,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return embedding.tolist()