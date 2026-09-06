from __future__ import annotations

from pathlib import Path


class ArtifactValidator:
    SUPPORTED = {
        ".docx",
        ".xlsx",
        ".pptx",
        ".pdf",
        ".py",
    }

    def validate(self, file_path: str) -> dict:
        path = Path(file_path)

        if not path.exists():
            return {
                "valid": False,
                "reason": "Artifact does not exist.",
            }

        if not path.is_file():
            return {
                "valid": False,
                "reason": "Artifact path is not a file.",
            }

        if path.suffix.lower() not in self.SUPPORTED:
            return {
                "valid": False,
                "reason": (
                    f"Unsupported artifact type: "
                    f"{path.suffix}"
                ),
            }

        if path.stat().st_size == 0:
            return {
                "valid": False,
                "reason": "Artifact is empty.",
            }

        return {
            "valid": True,
            "reason": "Artifact exists and is non-empty.",
            "path": str(path),
            "size": path.stat().st_size,
            "type": path.suffix.lower(),
        }