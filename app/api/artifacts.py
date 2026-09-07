from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.artifacts import ARTIFACT_ROOT


router = APIRouter(
    prefix="/artifacts",
    tags=["artifacts"],
)


@router.get("/download")
def download_artifact(filename: str):
    """
    Serve a previously generated artifact from data/artifacts/.

    Only the basename is accepted (any directory component is
    stripped) so this cannot be used to read arbitrary files
    outside the artifact directory.
    """

    safe_name = Path(filename).name

    if not safe_name:
        raise HTTPException(
            status_code=400,
            detail="filename is required.",
        )

    path = ARTIFACT_ROOT / safe_name

    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Artifact not found.",
        )

    return FileResponse(
        path=str(path),
        filename=safe_name,
    )
