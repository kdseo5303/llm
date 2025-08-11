# Movie Industry LLM Agent

An intelligent chatbot agent specialized in answering questions about the movie industry, including pre-production, production, and post-production stages.

## Features

- **Focused Knowledge**: Specialized in movie industry information only
- **Smart Context Retrieval**: Uses vector embeddings to find relevant information
- **Conversation Memory**: Maintains context across chat sessions
- **Source Attribution**: Shows which documents informed responses
- **RESTful API**: Easy integration with frontend applications
- **Beautiful Web Interface**: Modern, responsive chat interface

## Project Structure

```
llm/
├── backend/                 # FastAPI backend application
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core configuration and utilities
│   │   ├── models/         # Pydantic models
│   │   └── services/       # Business logic services
│   ├── data/               # Knowledge base data
│   └── main.py             # FastAPI application entry point
├── frontend/                # Web interface
│   └── index.html          # Chat interface
├── knowledge_base/          # Movie industry knowledge documents
├── requirements.txt         # Python dependencies
├── start_app.py            # Easy startup script
├── test_setup.py           # Setup verification script
├── env_template.txt         # Environment variables template
└── README.md               # This file
```

## Quick Start

### Option 1: Automated Startup (Recommended)
```bash
# 1. Install dependencies
pip3 install -r requirements.txt

# 2. Set up your OpenAI API key
cp env_template.txt .env
# Edit .env and add your OpenAI API key

# 3. Start the application
python3 start_app.py
```

### Option 2: Manual Startup
```bash
# 1. Install dependencies
pip3 install -r requirements.txt

# 2. Set up environment variables
cp env_template.txt .env
# Edit .env and add your OpenAI API key

# 3. Start backend
cd backend
uvicorn main:app --reload

# 4. Open frontend (in another terminal)
open frontend/index.html
```

## Setup Instructions

1. **Install Python dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp env_template.txt .env
   # Edit .env and add your OpenAI API key
   ```

3. **Verify setup:**
   ```bash
   python3 test_setup.py
   ```

4. **Start the application:**
   ```bash
   python3 start_app.py
   ```

## Usage

The agent is designed to answer questions about:
- **Pre-production**: Script development, casting, location scouting, budgeting
- **Production**: Filming, directing, cinematography, sound recording
- **Post-production**: Editing, visual effects, sound mixing, color grading

### Web Interface
- Open `frontend/index.html` in your browser
- Type questions about the movie industry
- View source attribution for responses
- Manage conversation history

### API Access
- **API documentation**: http://localhost:8000/docs
- **Chat endpoint**: http://localhost:8000/api/v1/chat
- **Knowledge management**: http://localhost:8000/api/v1/knowledge

## API Endpoints

### Chat
- `POST /api/v1/chat` - Send a message and get a response
- `GET /api/v1/chat/conversations` - List all conversations
- `GET /api/v1/chat/conversations/{id}` - Get conversation history
- `DELETE /api/v1/chat/conversations/{id}` - Delete conversation

### Knowledge Base
- `GET /api/v1/knowledge` - List all documents
- `POST /api/v1/knowledge` - Add new document
- `POST /api/v1/knowledge/upload-text` - Upload text file
- `GET /api/v1/knowledge/search` - Search documents
- `GET /api/v1/knowledge/stats` - Get knowledge base statistics

## Adding Knowledge

You can add your own movie industry knowledge by:

1. **Adding text files** to the `knowledge_base/` directory
2. **Using the API** to upload documents
3. **Organizing by category**: pre-production, production, post-production

The system automatically categorizes documents based on folder structure.

## Development Roadmap

- [x] Project structure setup
- [x] Backend API implementation
- [x] Knowledge base integration
- [x] LLM agent logic
- [x] Frontend chat interface
- [x] Basic source attribution
- [ ] Advanced analytics dashboard
- [ ] Multi-modal support (images, documents)
- [ ] User authentication and management
- [ ] Performance optimization

## Troubleshooting

### Common Issues

1. **Import errors**: Run `pip3 install -r requirements.txt`
2. **OpenAI API errors**: Check your `.env` file and API key
3. **Port conflicts**: Change port in `backend/main.py` or `start_app.py`
4. **Frontend not loading**: Ensure backend is running on port 8000

### Testing

Run the test script to verify your setup:
```bash
python3 test_setup.py
```

## Contributing

Feel free to add more movie industry knowledge documents or improve the codebase! 