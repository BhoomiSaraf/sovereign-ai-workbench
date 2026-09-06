from fastapi import APIRouter
from app.api.models import ChatRequest, ChatResponse

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)

@router.post("/", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Send a simple message to the semantic router/AI model.
    """
    
    # (Future step) Pass request.message to your semantic router here
    # For now, we return a mock response to test the API
    
    return ChatResponse(
        reply=f"I am a sovereign AI. I received your message: '{request.message}'. Processing entirely locally.",
        model_used="deepseek-r1:1.5b",
        external_calls=0
    )