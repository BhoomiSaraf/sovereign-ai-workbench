from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from fastapi import FastAPI

from app.api.artifacts import router as artifacts_router
from app.api.audit import router as audit_router
from app.api.chat import router as chat_router
from app.api.files import router as files_router
from app.api.knowledge import router as knowledge_router
from app.api.models import router as models_router
from app.api.system import router as system_router
from app.api.tasks import router as tasks_router


app = FastAPI(
    title="Sovereign AI Workbench",
    description=(
        "Local AI workbench for sensitive "
        "industrial and government workloads."
    ),
    version="0.1.0",
)

app.include_router(files_router)
app.include_router(knowledge_router)
app.include_router(models_router)
app.include_router(tasks_router)
app.include_router(chat_router)
app.include_router(artifacts_router)
app.include_router(audit_router)
app.include_router(system_router)

# Define the path to your compiled frontend folder
# Adjust this path based on where your 'dist' folder actually is
frontend_dist_path = os.path.join(os.path.dirname(__file__), "../../frontend/dist")

# Mount the assets folder (CSS, JS, images)
app.mount("/assets", StaticFiles(directory=f"{frontend_dist_path}/assets"), name="assets")

# Catch-all route to serve the React index.html for the UI
@app.get("/{catchall:path}")
def serve_react_app(catchall: str):
    return FileResponse(f"{frontend_dist_path}/index.html")