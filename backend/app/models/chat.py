from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class MessageRole(str, Enum):
    """Message roles in the conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatMessage(BaseModel):
    """Individual chat message model."""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None

class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = None
    include_sources: bool = True
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    use_fast_validation: bool = Field(default=True, description="Use fast validation for better performance. Set to False for comprehensive validation.")
    use_turbo_mode: bool = Field(default=False, description="Enable turbo mode for maximum speed. Skips web search and validation for instant responses.")

class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str
    conversation_id: str
    sources: Optional[List[Dict[str, Any]]] = None
    tokens_used: Optional[int] = None
    response_time: float
    validation: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class Conversation(BaseModel):
    """Conversation model for managing chat sessions."""
    id: str
    messages: List[ChatMessage] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None

class KnowledgeDocument(BaseModel):
    """Model for knowledge base documents."""
    id: str
    title: str
    content: str
    category: str  # pre-production, production, post-production
    tags: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None 