from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

# 1. Model for creating a new task
class TaskCreate(BaseModel):
    task_type: str = Field(..., description="e.g., 'coding', 'document_analysis'")
    prompt: str = Field(..., description="The user's instruction")
    file_id: Optional[str] = Field(None, description="ID of an uploaded file if applicable")

# 2. Model for what a Task looks like when returned to the UI
class TaskResponse(BaseModel):
    task_id: str
    status: str
    created_at: datetime
    result: Optional[str] = None
    artifacts: Optional[list] = [] # E.g., ['approval_note.docx']

# 3. Model for Chat Messages
class ChatRequest(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    reply: str
    model_used: str
    external_calls: int = 0 # To prove sovereignty