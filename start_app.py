#!/usr/bin/env python3
"""
Startup script for the Movie Industry LLM Agent.
This script will start the backend API and open the frontend in your browser.
"""

import subprocess
import time
import webbrowser
import os
import sys
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import fastapi
        import openai
        import chromadb
        print("✓ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Please run: pip3 install -r requirements.txt")
        return False

def check_env_file():
    """Check if .env file exists with OpenAI API key."""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  No .env file found!")
        print("Please create a .env file with your OpenAI API key:")
        print("OPENAI_API_KEY=your_api_key_here")
        print("\nYou can copy from env_template.txt")
        return False
    
    # Check if API key is set
    with open(env_file, 'r') as f:
        content = f.read()
        if 'your_openai_api_key_here' in content or 'OPENAI_API_KEY=' not in content:
            print("⚠️  Please set your OpenAI API key in the .env file")
            return False
    
    print("✓ Environment file configured")
    return True

def start_backend():
    """Start the FastAPI backend server."""
    print("🚀 Starting backend server...")
    
    # Change to backend directory
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("✗ Backend directory not found!")
        return None
    
    try:
        # Start the server in the background
        process = subprocess.Popen(
            ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a bit for server to start
        time.sleep(3)
        
        # Check if server is running
        if process.poll() is None:
            print("✓ Backend server started successfully")
            return process
        else:
            print("✗ Failed to start backend server")
            return None
            
    except Exception as e:
        print(f"✗ Error starting backend: {e}")
        return None

def open_frontend():
    """Open the frontend in the default browser."""
    frontend_file = Path("frontend/index.html")
    if frontend_file.exists():
        print("🌐 Opening frontend in browser...")
        webbrowser.open(f"file://{frontend_file.absolute()}")
        print("✓ Frontend opened")
    else:
        print("⚠️  Frontend file not found, you can manually open frontend/index.html")

def main():
    """Main startup function."""
    print("🎬 Movie Industry LLM Agent - Startup")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Check environment
    if not check_env_file():
        return
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        print("Failed to start backend. Exiting.")
        return
    
    # Wait a bit more for server to fully start
    time.sleep(2)
    
    # Open frontend
    open_frontend()
    
    print("\n" + "=" * 50)
    print("🎉 Application started successfully!")
    print("\nBackend API: http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    print("Frontend: frontend/index.html")
    print("\nTo stop the backend, press Ctrl+C in this terminal")
    print("=" * 50)
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
            if backend_process.poll() is not None:
                print("Backend server stopped unexpectedly")
                break
    except KeyboardInterrupt:
        print("\n🛑 Stopping application...")
        backend_process.terminate()
        print("✓ Application stopped")

if __name__ == "__main__":
    main() 