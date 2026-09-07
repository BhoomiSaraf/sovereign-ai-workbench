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


DOCUMENT_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt",
}

IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
}

ALLOWED_EXTENSIONS = DOCUMENT_EXTENSIONS | IMAGE_EXTENSIONS


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
):
    """
    Upload a local document or image.

    Documents (PDF/DOCX/TXT) are ingested into the local
    sovereign knowledge base. Images are stored for use as
    task attachments (vision analysis) and are not text-ingested.
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

    if extension not in ALLOWED_EXTENSIONS:
        return {
            "status": "error",
            "message": (
                f"Unsupported file type: {extension}. "
                f"Supported types: "
                f"{', '.join(sorted(ALLOWED_EXTENSIONS))}"
            ),
        }

    file_id = uuid4().hex

    destination = (
        UPLOAD_DIRECTORY
        / f"{file_id}{extension}"
    )

    content = await file.read()

    if not content:
        return {
            "status": "error",
            "message": "Uploaded file is empty.",
        }

    destination.write_bytes(
        content
    )

    if extension in IMAGE_EXTENSIONS:
        return {
            "status": "success",
            "file_id": file_id,
            "filename": file.filename,
            "ingestion": {
                "status": "skipped",
                "reason": (
                    "Images are not ingested into the text "
                    "knowledge base; attach them to a task for "
                    "vision analysis instead."
                ),
            },
        }

    try:
        ingester = KnowledgeIngester()

        result = ingester.ingest_file(
            str(destination),
            metadata={
                "file_id": file_id,
                "original_filename": file.filename,
            },
        )

        return {
            "status": "success",
            "file_id": file_id,
            "filename": file.filename,
            "ingestion": result,
        }

    except Exception as exc:
        return {
            "status": "error",
            "file_id": file_id,
            "filename": file.filename,
            "message": str(exc),
        }