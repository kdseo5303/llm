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
        print(f"🚀 Starting chat request processing for message: {request.message[:100]}...")
        
        try:
            # Get or create conversation
            conversation_id = request.conversation_id or str(uuid.uuid4())
            print(f"📝 Conversation ID: {conversation_id}")
            conversation = self._get_or_create_conversation(conversation_id)
            print(f"✅ Conversation retrieved/created successfully")
            
            # Add user message to conversation
            user_message = ChatMessage(
                role=MessageRole.USER,
                content=request.message
            )
            conversation.messages.append(user_message)
            print(f"✅ User message added to conversation")
            
            # Validate if question is movie industry related
            print(f"🔍 Validating movie industry question...")
            try:
                is_movie_question = self.llm_service.validate_movie_industry_question(request.message)
                print(f"✅ Movie industry validation: {is_movie_question}")
            except Exception as e:
                print(f"❌ Error in movie industry validation: {str(e)}")
                is_movie_question = True  # Default to allowing the question
            
            if not is_movie_question:
                response_content = (
                    "I'm specialized in movie industry topics. Please ask me about "
                    "pre-production, production, or post-production processes, filmmaking "
                    "techniques, industry practices, or any other movie-related questions."
                )
                print(f"✅ Non-movie question handled")
            else:
                # Search for relevant context in local knowledge base
                print(f"🔍 Searching local knowledge base...")
                try:
                    local_context_results = await self.knowledge_service.search_context(
                        request.message, 
                        max_results=3
                    )
                    print(f"✅ Local search complete: {len(local_context_results)} results")
                except Exception as e:
                    print(f"❌ Error in local search: {str(e)}")
                    local_context_results = []
                
                # Search for current information online
                print(f"🔍 Searching web for current information...")
                try:
                    # Check if turbo mode is enabled (skip web search for speed)
                    use_turbo_mode = getattr(request, 'use_turbo_mode', False)
                    
                    if use_turbo_mode:
                        print(f"🚀 Turbo mode: Skipping web search for maximum speed")
                        web_search_results = []
                    else:
                        web_search_results = await self.web_search_service.search_movie_industry(
                            request.message,
                            max_results=2
                        )
                        print(f"✅ Web search complete: {len(web_search_results)} results")
                except Exception as e:
                    print(f"❌ Error in web search: {str(e)}")
                    web_search_results = []
                
                # Combine local and web results
                context_results = local_context_results + web_search_results
                print(f"✅ Combined context: {len(context_results)} total results")
                
                # Prepare context for LLM
                print(f"🔍 Preparing context for LLM...")
                try:
                    if use_turbo_mode:
                        # Turbo mode: minimal context, let GPT do the heavy lifting
                        context = "You are a movie industry expert. Use your knowledge to answer the question. If you need to mention specific sources, provide them in a natural way."
                        print(f"🚀 Turbo mode: Using minimal context for maximum speed")
                    else:
                        context = self._prepare_context(context_results)
                        print(f"✅ Context prepared: {len(context)} characters")
                        print(f"🔍 Context preview: {context[:200]}...")
                except Exception as e:
                    print(f"❌ Error preparing context: {str(e)}")
                    import traceback
                    print(f"❌ Context preparation traceback: {traceback.format_exc()}")
                    raise e
                
                # Generate LLM response
                print(f"🔍 Generating LLM response...")
                try:
                    print(f"🔍 Messages being sent to LLM: {len(conversation.messages)} messages")
                    print(f"🔍 Last few messages: {[msg.content[:50] + '...' for msg in conversation.messages[-3:]]}")
                    print(f"🔍 Context length: {len(context)} characters")
                    print(f"🔍 Temperature: {request.temperature}")
                    print(f"🔍 Max tokens: {request.max_tokens}")
                    
                    llm_response = self.llm_service.generate_response(
                        messages=conversation.messages[-settings.max_conversation_history:],
                        context=context,
                        temperature=request.temperature,
                        max_tokens=request.max_tokens,
                        turbo_mode=use_turbo_mode
                    )
                    print(f"✅ LLM response generated successfully")
                    
                    response_content = llm_response['response']
                    tokens_used = llm_response['tokens_used']
                    print(f"✅ Response content extracted: {len(response_content)} characters")
                    print(f"🔍 Response preview: {response_content[:200]}...")
                except Exception as e:
                    print(f"❌ Error in LLM response generation: {str(e)}")
                    import traceback
                    print(f"❌ LLM error traceback: {traceback.format_exc()}")
                    raise e
                
                # Validate response to prevent hallucinations
                print(f"🔍 Validating response...")
                try:
                    # Use fast validation by default for better performance
                    # Full validation can be enabled via request parameter if needed
                    use_fast_validation = getattr(request, 'use_fast_validation', True)
                    
                    if use_turbo_mode:
                        print(f"🚀 Turbo mode: Skipping validation for maximum speed")
                        validation_result = {
                            'is_valid': True,
                            'confidence_score': 0.9,
                            'warnings': ['🚀 Turbo mode: Response generated without external validation for maximum speed'],
                            'source_coverage': 1.0,
                            'unverified_claims': [],
                            'recommendations': [],
                            'source_types': {'local': 0, 'web': 0}
                        }
                    else:
                        print(f"🔍 Using {'fast' if use_fast_validation else 'full'} validation mode")
                        
                        validation_result = self.response_validator.validate_response(
                            response_content, 
                            context_results, 
                            request.message,
                            fast_mode=use_fast_validation
                        )
                        print(f"✅ Response validation complete")
                except Exception as e:
                    print(f"❌ Error in response validation: {str(e)}")
                    import traceback
                    print(f"❌ Validation error traceback: {traceback.format_exc()}")
                    # Create a default validation result to continue
                    validation_result = {'warnings': [], 'confidence_score': 0.8}
                
                # Add validation summary to response if there are warnings
                if validation_result['warnings'] or validation_result['confidence_score'] < 0.8:
                    print(f"🔍 Adding validation summary...")
                    try:
                        validation_summary = self.response_validator.generate_validation_summary(validation_result)
                        response_content += f"\n\n--- Validation Summary ---\n{validation_summary}"
                        
                        # If confidence is too low, add a warning
                        if validation_result['confidence_score'] < 0.7:
                            response_content = f"⚠️ WARNING: This response has low confidence and may contain unverified information.\n\n{response_content}"
                        print(f"✅ Validation summary added")
                    except Exception as e:
                        print(f"❌ Error adding validation summary: {str(e)}")
            
            # Set tokens_used if not already set
            if 'tokens_used' not in locals():
                tokens_used = None
                print(f"🔍 Tokens used not set, defaulting to None")
            
            # Add assistant response to conversation
            print(f"🔍 Adding assistant response to conversation...")
            try:
                assistant_message = ChatMessage(
                    role=MessageRole.ASSISTANT,
                    content=response_content
                )
                conversation.messages.append(assistant_message)
                print(f"✅ Assistant message added to conversation")
            except Exception as e:
                print(f"❌ Error adding assistant message: {str(e)}")
                import traceback
                print(f"❌ Assistant message error traceback: {traceback.format_exc()}")
                raise e
            
            # Update conversation timestamp
            conversation.updated_at = datetime.now()
            print(f"✅ Conversation timestamp updated")
            
            # Prepare sources if requested
            sources = None
            if request.include_sources:
                print(f"🔍 Preparing sources...")
                try:
                    if use_turbo_mode:
                        # In turbo mode, extract citations from GPT's response
                        print(f"🚀 Turbo mode: Extracting citations from GPT response")
                        extracted_citations = self.response_validator.extract_citations_from_response(response_content)
                        if extracted_citations:
                            sources = extracted_citations
                            print(f"✅ Extracted {len(extracted_citations)} citations from GPT response")
                        else:
                            sources = []
                            print(f"⚠️ No citations found in GPT response")
                    else:
                        # Standard mode: use context results
                        sources = self._format_sources(context_results)
                        print(f"✅ Sources prepared: {len(sources)} sources")
                except Exception as e:
                    print(f"❌ Error preparing sources: {str(e)}")
                    sources = []
            
            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds()
            print(f"✅ Chat processing complete in {response_time:.2f}s")
            
            # Create final response
            print(f"🔍 Creating final ChatResponse...")
            try:
                final_response = ChatResponse(
                    response=response_content,
                    conversation_id=conversation_id,
                    sources=sources,
                    tokens_used=tokens_used,
                    response_time=response_time,
                    validation=validation_result if 'validation_result' in locals() else None
                )
                print(f"✅ ChatResponse created successfully")
                print(f"🔍 Final response details:")
                print(f"   - Response length: {len(final_response.response)} characters")
                print(f"   - Conversation ID: {final_response.conversation_id}")
                print(f"   - Sources count: {len(final_response.sources) if final_response.sources else 0}")
                print(f"   - Response time: {final_response.response_time:.2f}s")
                return final_response
            except Exception as e:
                print(f"❌ Error creating ChatResponse: {str(e)}")
                import traceback
                print(f"❌ ChatResponse creation traceback: {traceback.format_exc()}")
                raise e
                
        except Exception as e:
            print(f"❌ Fatal error in process_chat_request: {str(e)}")
            import traceback
            print(f"❌ Full traceback: {traceback.format_exc()}")
            raise e
    
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
        print(f"🔍 _prepare_context called with {len(context_results)} results")
        
        if not context_results:
            print(f"🔍 No context results, returning default message")
            return "No specific movie industry context found for this question."
        
        context_parts = []
        for i, result in enumerate(context_results):
            print(f"🔍 Processing result {i+1}: {result.get('title', 'No title')}")
            print(f"🔍 Result keys: {list(result.keys())}")
            print(f"🔍 Result content preview: {str(result.get('content', 'No content'))[:100]}...")
            
            try:
                title = result.get('title', 'Unknown Source')
                url = result.get('url', result.get('href', ''))
                content = result.get('content', result.get('snippet', 'No content available'))
                
                # Include URL in context if available
                if url:
                    context_parts.append(
                        f"From '{title}' (Source: {url}):\n{content[:500]}..."
                    )
                else:
                    context_parts.append(
                        f"From '{title}':\n{content[:500]}..."
                    )
                print(f"✅ Result {i+1} processed successfully")
            except Exception as e:
                print(f"❌ Error processing result {i+1}: {str(e)}")
                # Add a fallback for this result
                context_parts.append(
                    f"From '{result.get('title', 'Unknown Source')}':\n{str(result)[:500]}..."
                )
        
        final_context = "\n\n".join(context_parts)
        print(f"🔍 Final context length: {len(final_context)} characters")
        print(f"🔍 Final context preview: {final_context[:200]}...")
        
        return final_context
    
    def _format_sources(self, context_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format source information for response."""
        print(f"🔍 _format_sources called with {len(context_results)} results")
        sources = []
        
        for i, result in enumerate(context_results):
            print(f"🔍 Processing source {i+1}: {result.get('title', 'No title')}")
            try:
                source = {
                    'title': result.get('title', 'Unknown Source'),
                    'url': result.get('url', result.get('href', '')),
                    'source_type': result.get('source_type', 'web_search'),
                    'relevance_score': round(result.get('relevance_score', 0.8), 3) if result.get('relevance_score') else 0.8
                }
                sources.append(source)
                print(f"✅ Source {i+1} formatted successfully")
            except Exception as e:
                print(f"❌ Error formatting source {i+1}: {str(e)}")
                # Add a fallback source
                sources.append({
                    'title': result.get('title', 'Unknown Source'),
                    'url': result.get('url', result.get('href', '')),
                    'source_type': 'web_search',
                    'relevance_score': 0.8
                })
        
        print(f"✅ Sources formatted: {len(sources)} sources")
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