from fastapi import FastAPI

from app.api.files import router as files_router
from app.api.knowledge import (
    router as knowledge_router,
)
from app.api.tasks import router as tasks_router
from app.api.chat import router as chat_router


app = FastAPI(
    title="Sovereign AI Workbench",
    description=(
        "Local AI workbench for sensitive "
        "industrial and government workloads."
    ),
    version="0.1.0",
)


app.include_router(
    files_router
)

app.include_router(
    knowledge_router
)

app.include_router(
    tasks_router
)

app.include_router(
    chat_router
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "sovereign": True,
        "external_network_required": False,
    }