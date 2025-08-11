from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Application settings and configuration."""
    
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = "gpt-4"
    openai_temperature: float = 0.7
    openai_max_tokens: int = 1000
    
    # Application Configuration
    app_name: str = "Movie Industry LLM Agent"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Knowledge Base Configuration
    knowledge_base_path: str = "knowledge_base"
    vector_db_path: str = "backend/data/vector_db"
    max_context_length: int = 4000
    
    # Chat Configuration
    max_conversation_history: int = 10
    system_prompt: str = """You are an expert AI assistant specializing in the movie industry. 
    You have deep knowledge of pre-production, production, and post-production processes.
    
    Your expertise includes:
    - Pre-production: Script development, casting, location scouting, budgeting, scheduling
    - Production: Filming, directing, cinematography, sound recording, set management
    - Post-production: Editing, visual effects, sound mixing, color grading, distribution
    
    Always provide accurate, helpful information about movie industry topics. If asked about 
    something outside the movie industry, politely redirect the conversation back to film-related topics.
    
    Be concise but informative, and cite specific examples when possible."""
    
    class Config:
        env_file = ".env"

settings = Settings() 