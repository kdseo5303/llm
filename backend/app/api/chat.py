from fastapi import APIRouter, HTTPException, Depends
from typing import List
from ..models.chat import ChatRequest, ChatResponse, Conversation
from ..services.chat_service import ChatService
from ..services.knowledge_service import KnowledgeService
from datetime import datetime

router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize services
chat_service = ChatService()
knowledge_service = KnowledgeService()

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message and get a response from the movie industry LLM agent.
    
    Args:
        request: Chat request containing user message and options
        
    Returns:
        Chat response with AI-generated answer and metadata
    """
    print(f"🚀 Chat endpoint called")
    print(f"🔍 Request message: {request.message[:100]}...")
    print(f"🔍 Request conversation_id: {request.conversation_id}")
    print(f"🔍 Request temperature: {request.temperature}")
    print(f"🔍 Request max_tokens: {request.max_tokens}")
    print(f"🔍 Request include_sources: {request.include_sources}")
    
    try:
        print(f"🔍 Calling chat_service.process_chat_request...")
        response = await chat_service.process_chat_request(request)
        print(f"✅ Chat service returned response successfully")
        print(f"🔍 Response details:")
        print(f"   - Response length: {len(response.response)}")
        print(f"   - Conversation ID: {response.conversation_id}")
        print(f"   - Sources count: {len(response.sources) if response.sources else 0}")
        print(f"   - Response time: {response.response_time}")
        return response
    except Exception as e:
        print(f"❌ Error in chat endpoint: {str(e)}")
        import traceback
        print(f"❌ Chat endpoint error traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")

@router.get("/conversations", response_model=List[Conversation])
async def get_conversations():
    """Get all chat conversations."""
    try:
        return await chat_service.get_all_conversations()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving conversations: {str(e)}")

@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    """Get a specific conversation by ID."""
    try:
        conversation = await chat_service.get_conversation_history(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving conversation: {str(e)}")

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    try:
        success = await chat_service.delete_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"message": "Conversation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting conversation: {str(e)}")

@router.post("/conversations/{conversation_id}/clear")
async def clear_conversation(conversation_id: str):
    """Clear all messages from a conversation while keeping the conversation ID."""
    try:
        conversation = await chat_service.get_conversation_history(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Clear messages but keep conversation
        conversation.messages = []
        conversation.updated_at = datetime.now()
        
        return {"message": "Conversation cleared successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing conversation: {str(e)}") 