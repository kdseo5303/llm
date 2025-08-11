import openai
from typing import List, Dict, Any, Optional
import time
from ..core.config import settings
from ..models.chat import ChatMessage, MessageRole

class LLMService:
    """Service for interacting with OpenAI's LLM API."""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.temperature = settings.openai_temperature
        self.max_tokens = settings.openai_max_tokens
    
    def generate_response(
        self,
        messages: List[ChatMessage],
        context: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a response from the LLM.
        
        Args:
            messages: List of conversation messages
            context: Additional context from knowledge base
            temperature: Response creativity (0.0 to 2.0)
            max_tokens: Maximum tokens in response
            
        Returns:
            Dictionary containing response and metadata
        """
        start_time = time.time()
        
        # Prepare messages for OpenAI API
        openai_messages = []
        
        # Add system message with movie industry focus
        openai_messages.append({
            "role": "system",
            "content": settings.system_prompt
        })
        
        # Add context if provided
        if context:
            openai_messages.append({
                "role": "system",
                "content": f"Additional context from knowledge base:\n{context}"
            })
        
        # Add conversation messages
        for msg in messages:
            openai_messages.append({
                "role": msg.role.value,
                "content": msg.content
            })
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens
            )
            
            response_time = time.time() - start_time
            
            return {
                "response": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens,
                "response_time": response_time,
                "model": self.model
            }
            
        except Exception as e:
            raise Exception(f"Error generating LLM response: {str(e)}")
    
    def validate_movie_industry_question(self, question: str) -> bool:
        """
        Basic validation to ensure question is movie industry related.
        This is a simple keyword-based approach that can be enhanced.
        """
        movie_keywords = [
            'film', 'movie', 'cinema', 'production', 'director', 'actor', 'actress',
            'script', 'screenplay', 'camera', 'editing', 'post-production', 'pre-production',
            'casting', 'location', 'budget', 'schedule', 'crew', 'sound', 'lighting',
            'visual effects', 'color grading', 'distribution', 'box office'
        ]
        
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in movie_keywords)
    
    def create_focused_prompt(self, question: str, context: str) -> str:
        """
        Create a focused prompt that combines the user question with relevant context.
        """
        return f"""Based on the following movie industry knowledge, please answer this question: {question}

Relevant Information:
{context}

Please provide a comprehensive answer that focuses specifically on the movie industry aspects. If the question touches on areas outside film production, focus on the film-related elements.""" 