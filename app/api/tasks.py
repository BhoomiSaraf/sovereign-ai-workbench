from fastapi import APIRouter, HTTPException
from uuid import uuid4
from datetime import datetime
from app.api.models import TaskCreate, TaskResponse

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)

# Temporary in-memory dictionary to act as our SQLite database placeholder
# In the next iteration, you will replace this with SQL queries!
fake_sqlite_db = {}

@router.post("/start", response_model=TaskResponse)
async def start_task(task_request: TaskCreate):
    """
    Receive a task from the UI, save it to the DB, and trigger the AI.
    """
    task_id = uuid4().hex
    
    # 1. Create the database record
    new_task = {
        "task_id": task_id,
        "status": "running",
        "created_at": datetime.now(),
        "task_type": task_request.task_type,
        "prompt": task_request.prompt,
        "result": None
    }
    
    # 2. Save to our "SQLite" database
    fake_sqlite_db[task_id] = new_task
    
    # 3. (Future step) Here is where you will call LangGraph to start working!
    
    return new_task

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    """
    The UI will constantly call this endpoint to check if the AI is done.
    """
    task = fake_sqlite_db.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found in database")
    
    return task