from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, UploadFile

from app.rag.ingest import KnowledgeIngester


router = APIRouter(
    prefix="/files",
    tags=["files"],
)


UPLOAD_DIRECTORY = Path(
    "data/uploads"
)

UPLOAD_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
)


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
):
    """
    Upload a local document and ingest it into
    the sovereign knowledge base.
    """

    if not file.filename:
        return {
            "status": "error",
            "message": "Filename is required.",
        }

    extension = (
        Path(file.filename)
        .suffix
        .lower()
    )

    allowed_extensions = {
        ".pdf",
        ".docx",
        ".txt",
    }

    if extension not in allowed_extensions:
        return {
            "status": "error",
            "message": (
                f"Unsupported file type: {extension}"
            ),
        }

    file_id = uuid4().hex

    safe_name = (
        f"{file_id}{extension}"
    )

    destination = (
        UPLOAD_DIRECTORY
        / safe_name
    )

    content = await file.read()

    destination.write_bytes(
        content
    )

    try:
        ingester = KnowledgeIngester()

        result = ingester.ingest_file(
            str(destination),
            metadata={
                "original_filename": (
                    file.filename
                ),
                "file_id": file_id,
            },
        )

        return {
            "status": "success",
            "file_id": file_id,
            "filename": file.filename,
            "ingestion": result,
        }

    except Exception as exc:

        # Keep the uploaded file available for
        # debugging/audit purposes.
        return {
            "status": "error",
            "file_id": file_id,
            "filename": file.filename,
            "message": str(exc),
        }