import openai
from typing import List, Dict, Any, Optional
import time
from ..core.config import settings
from ..models.chat import ChatMessage, MessageRole
import hashlib

class LLMService:
    """Service for interacting with OpenAI's LLM API."""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.temperature = settings.openai_temperature
        self.max_tokens = settings.openai_max_tokens
        
        # Simple response cache for repeated questions
        self._response_cache = {}
        self._cache_ttl = 600  # 10 minutes
    
    def generate_response(
        self,
        messages: List[ChatMessage],
        context: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[float] = None,
        turbo_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a response from the LLM.
        
        Args:
            messages: List of conversation messages
            context: Additional context from knowledge base
            temperature: Response creativity (0.0 to 2.0)
            max_tokens: Maximum tokens in response
            turbo_mode: If True, use optimized settings for maximum speed
            
        Returns:
            Dictionary containing response and metadata
        """
        start_time = time.time()
        print(f"🚀 LLM generate_response called (turbo_mode: {turbo_mode})")
        print(f"🔍 Messages count: {len(messages)}")
        print(f"🔍 Context provided: {context is not None}")
        print(f"🔍 Context length: {len(context) if context else 0}")
        print(f"🔍 Temperature: {temperature}")
        print(f"🔍 Max tokens: {max_tokens}")
        print(f"🔍 OpenAI API key length: {len(settings.openai_api_key) if settings.openai_api_key else 0}")
        
        # Check if API key is set
        if not settings.openai_api_key:
            print(f"❌ ERROR: OpenAI API key is not set!")
            raise Exception("OpenAI API key is not configured. Please set OPENAI_API_KEY in your environment.")
        
        # Check cache for similar requests
        cache_key = self._generate_cache_key(messages, context, temperature, max_tokens, turbo_mode)
        if cache_key in self._response_cache:
            cached_result = self._response_cache[cache_key]
            if time.time() - cached_result.get('_timestamp', 0) < self._cache_ttl:
                print(f"✅ Using cached LLM response")
                cached_result['response_time'] = 0.1  # Fast cache access
                return {k: v for k, v in cached_result.items() if not k.startswith('_')}
        
        # Prepare messages for OpenAI API
        openai_messages = []
        
        if turbo_mode:
            # Turbo mode: simplified, fast system prompt with citation requirements
            system_prompt = """You are a movie industry expert AI. Provide accurate, helpful answers about film production, budgeting, scheduling, and industry practices.

IMPORTANT: Always include relevant citations and source links in your responses. When mentioning specific information, cite sources like:
- Industry reports: "According to [Report Name] (link if available)"
- Film organizations: "Per [Organization Name] (link if available)"  
- Industry publications: "As stated in [Publication] (link if available)"
- Professional associations: "According to [Association] (link if available)"

For web sources, provide the full URL when possible. For industry standards and practices, mention the relevant organizations or publications.

Keep responses concise but informative, and always cite your sources naturally within the text."""
            print(f"🚀 Turbo mode: Using citation-focused system prompt for speed")
            # Force faster model and settings for turbo mode
            model = "gpt-3.5-turbo"  # Always use faster model in turbo mode
            max_tokens = 600  # Reduced for speed
            temperature = 0.3  # Lower for more focused responses
        else:
            system_prompt = settings.system_prompt
            print(f"🔍 Standard mode: Using full system prompt")
            model = self.model
            max_tokens = max_tokens or self.max_tokens
            temperature = temperature or self.temperature
        
        print(f"🔍 System prompt length: {len(system_prompt)}")
        openai_messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        # Add context if provided
        if context and not turbo_mode:
            context_message = f"Additional context from knowledge base:\n{context}"
            print(f"🔍 Context message length: {len(context_message)}")
            openai_messages.append({
                "role": "system",
                "content": context_message
            })
        
        # Add conversation messages
        for i, msg in enumerate(messages):
            print(f"🔍 Adding message {i+1}: role={msg.role.value}, content_length={len(msg.content)}")
            openai_messages.append({
                "role": msg.role.value,
                "content": msg.content
            })
        
        print(f"🔍 Total OpenAI messages: {len(openai_messages)}")
        print(f"🔍 Model: {self.model}")
        
        try:
            print(f"🔍 Calling OpenAI API...")
            
            response = self.client.chat.completions.create(
                model=model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            print(f"✅ OpenAI API call successful")
            
            response_time = time.time() - start_time
            
            result = {
                "response": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens,
                "response_time": response_time,
                "model": model,
                "turbo_mode": turbo_mode
            }
            
            print(f"✅ Response generated successfully")
            print(f"🔍 Response length: {len(result['response'])} characters")
            print(f"🔍 Tokens used: {result['tokens_used']}")
            print(f"🔍 Response time: {result['response_time']:.2f}s")
            print(f"🔍 Turbo mode: {turbo_mode}")
            
            # Cache the result
            result['_timestamp'] = time.time()
            self._response_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            print(f"❌ Error calling OpenAI API: {str(e)}")
            import traceback
            print(f"❌ OpenAI API error traceback: {traceback.format_exc()}")
            raise Exception(f"Error generating LLM response: {str(e)}")
    
    def _generate_cache_key(self, messages: List[Dict[str, str]], context: str, temperature: float, max_tokens: int, turbo_mode: bool) -> str:
        """Generate a cache key for the request."""
        # Include mode in cache key to separate turbo from standard responses
        mode_suffix = "_turbo" if turbo_mode else "_standard"
        content = f"{str(messages)}{context}{temperature}{max_tokens}{mode_suffix}"
        return hashlib.md5(content.encode()).hexdigest()
    
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