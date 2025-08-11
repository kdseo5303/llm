import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..models.chat import ChatMessage, MessageRole, ChatRequest, ChatResponse, Conversation
from .llm_service import LLMService
from .knowledge_service import KnowledgeService
from .response_validator import ResponseValidator
from .web_search_service import WebSearchService
from ..core.config import settings

class ChatService:
    """Service for managing chat conversations and generating responses."""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.knowledge_service = KnowledgeService()
        self.response_validator = ResponseValidator()
        self.web_search_service = WebSearchService()
        self.conversations: Dict[str, Conversation] = {}
    
    async def process_chat_request(self, request: ChatRequest) -> ChatResponse:
        """
        Process a chat request and generate a response.
        
        Args:
            request: Chat request containing user message and options
            
        Returns:
            Chat response with AI-generated answer
        """
        start_time = datetime.now()
        
        # Get or create conversation
        conversation_id = request.conversation_id or str(uuid.uuid4())
        conversation = self._get_or_create_conversation(conversation_id)
        
        # Add user message to conversation
        user_message = ChatMessage(
            role=MessageRole.USER,
            content=request.message
        )
        conversation.messages.append(user_message)
        
        # Validate if question is movie industry related
        if not self.llm_service.validate_movie_industry_question(request.message):
            response_content = (
                "I'm specialized in movie industry topics. Please ask me about "
                "pre-production, production, or post-production processes, filmmaking "
                "techniques, industry practices, or any other movie-related questions."
            )
        else:
            # Search for relevant context in local knowledge base
            local_context_results = await self.knowledge_service.search_context(
                request.message, 
                max_results=3
            )
            
            # Search for current information online
            web_search_results = await self.web_search_service.search_movie_industry(
                request.message,
                max_results=2
            )
            
            # Combine local and web results
            context_results = local_context_results + web_search_results
            
            # Prepare context for LLM
            context = self._prepare_context(context_results)
            
            # Generate LLM response
            llm_response = await self.llm_service.generate_response(
                messages=conversation.messages[-settings.max_conversation_history:],
                context=context,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            response_content = llm_response['response']
            tokens_used = llm_response['tokens_used']
            
            # Validate response to prevent hallucinations
            validation_result = self.response_validator.validate_response(
                response_content, 
                context_results, 
                request.message
            )
            
            # Add validation summary to response if there are warnings
            if validation_result['warnings'] or validation_result['confidence_score'] < 0.8:
                validation_summary = self.response_validator.generate_validation_summary(validation_result)
                response_content += f"\n\n--- Validation Summary ---\n{validation_summary}"
                
                # If confidence is too low, add a warning
                if validation_result['confidence_score'] < 0.7:
                    response_content = f"⚠️ WARNING: This response has low confidence and may contain unverified information.\n\n{response_content}"
        
        # Set tokens_used if not already set
        if 'tokens_used' not in locals():
            tokens_used = None
        
        # Add assistant response to conversation
        assistant_message = ChatMessage(
            role=MessageRole.ASSISTANT,
            content=response_content
        )
        conversation.messages.append(assistant_message)
        
        # Update conversation timestamp
        conversation.updated_at = datetime.now()
        
        # Prepare sources if requested
        sources = None
        if request.include_sources and 'context_results' in locals():
            sources = self._format_sources(context_results)
        
        # Calculate response time
        response_time = (datetime.now() - start_time).total_seconds()
        
        return ChatResponse(
            response=response_content,
            conversation_id=conversation_id,
            sources=sources,
            tokens_used=tokens_used,
            response_time=response_time,
            validation=validation_result if 'validation_result' in locals() else None
        )
    
    def _get_or_create_conversation(self, conversation_id: str) -> Conversation:
        """Get existing conversation or create a new one."""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = Conversation(
                id=conversation_id,
                messages=[]
            )
        return self.conversations[conversation_id]
    
    def _prepare_context(self, context_results: List[Dict[str, Any]]) -> str:
        """Prepare context string from search results."""
        if not context_results:
            return "No specific movie industry context found for this question."
        
        context_parts = []
        for result in context_results:
            context_parts.append(
                f"From '{result['title']}' ({result['category']}):\n{result['content'][:500]}..."
            )
        
        return "\n\n".join(context_parts)
    
    def _format_sources(self, context_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format source information for response."""
        sources = []
        for result in context_results:
            sources.append({
                'title': result['title'],
                'category': result['category'],
                'relevance_score': round(result['relevance_score'], 3)
            })
        return sources
    
    async def get_conversation_history(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation history by ID."""
        return self.conversations.get(conversation_id)
    
    async def get_all_conversations(self) -> List[Conversation]:
        """Get all conversations."""
        return list(self.conversations.values())
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False
    
    def _truncate_conversation_history(self, conversation: Conversation):
        """Keep only the most recent messages within the limit."""
        if len(conversation.messages) > settings.max_conversation_history:
            conversation.messages = conversation.messages[-settings.max_conversation_history:] 