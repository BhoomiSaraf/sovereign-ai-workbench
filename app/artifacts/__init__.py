from pathlib import Path


ARTIFACT_ROOT = Path("data/artifacts")
ARTIFACT_ROOT.mkdir(
    parents=True,
    exist_ok=True,
)


def artifact_path(filename: str) -> Path:
    path = ARTIFACT_ROOT / filename
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    return path