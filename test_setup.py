#!/usr/bin/env python3
"""
Simple test script to verify the movie industry LLM agent setup.
Run this to check if all dependencies are properly installed.
"""

import sys
import os

def test_imports():
    """Test if all required packages can be imported."""
    print("Testing package imports...")
    
    try:
        import fastapi
        print("✓ FastAPI imported successfully")
    except ImportError as e:
        print(f"✗ FastAPI import failed: {e}")
        return False
    
    try:
        import openai
        print("✓ OpenAI imported successfully")
    except ImportError as e:
        print(f"✗ OpenAI import failed: {e}")
        return False
    
    try:
        import chromadb
        print("✓ ChromaDB imported successfully")
    except ImportError as e:
        print(f"✗ ChromaDB import failed: {e}")
        return False
    
    try:
        import pydantic
        print("✓ Pydantic imported successfully")
    except ImportError as e:
        print(f"✗ Pydantic import failed: {e}")
        return False
    
    return True

def test_config():
    """Test if configuration can be loaded."""
    print("\nTesting configuration...")
    
    try:
        # Add the backend directory to Python path
        sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
        
        from app.core.config import settings
        print("✓ Configuration loaded successfully")
        print(f"  App Name: {settings.app_name}")
        print(f"  OpenAI Model: {settings.openai_model}")
        print(f"  Knowledge Base Path: {settings.knowledge_base_path}")
        return True
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
        return False

def test_knowledge_base():
    """Test if knowledge base files exist."""
    print("\nTesting knowledge base...")
    
    knowledge_path = "knowledge_base"
    if os.path.exists(knowledge_path):
        print(f"✓ Knowledge base directory exists: {knowledge_path}")
        
        # Check for sample documents
        categories = ['pre-production', 'production', 'post-production']
        for category in categories:
            category_path = os.path.join(knowledge_path, category)
            if os.path.exists(category_path):
                files = [f for f in os.listdir(category_path) if f.endswith('.txt')]
                print(f"  ✓ {category}: {len(files)} document(s)")
            else:
                print(f"  ✗ {category}: directory not found")
        
        return True
    else:
        print(f"✗ Knowledge base directory not found: {knowledge_path}")
        return False

def main():
    """Run all tests."""
    print("Movie Industry LLM Agent - Setup Test")
    print("=" * 50)
    
    all_passed = True
    
    # Test imports
    if not test_imports():
        all_passed = False
    
    # Test configuration
    if not test_config():
        all_passed = False
    
    # Test knowledge base
    if not test_knowledge_base():
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ All tests passed! Setup looks good.")
        print("\nNext steps:")
        print("1. Copy env_template.txt to .env and add your OpenAI API key")
        print("2. Run: cd backend && uvicorn main:app --reload")
        print("3. Open http://localhost:8000/docs to test the API")
    else:
        print("✗ Some tests failed. Please check the errors above.")
        print("\nCommon solutions:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Check Python version (3.8+ required)")
        print("3. Verify file structure and permissions")
    
    return all_passed

if __name__ == "__main__":
    main() 