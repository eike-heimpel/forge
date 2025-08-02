# Forge AI Service

FastAPI backend service for Forge - handles LLM processing and AI synthesis for team collaboration.

## Features

- **Synthesis Endpoint**: `/api/synthesize` - Processes team conversations and generates comprehensive briefings
- **Chat Endpoint**: `/api/chat` - Handles individual questions and context additions
- **MongoDB Integration**: Stores and retrieves forge state data
- **OpenRouter LLM**: Uses OpenRouter API for AI text generation

## Development Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   export MONGO_URI="your_mongodb_connection_string"
   export OPENROUTER_API_KEY="your_openrouter_api_key"
   export FORGE_AI_API_KEY="your_api_key_for_authentication"
   ```

3. **Run the service:**
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Access the API:**
   - API docs: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

## Deployment (Fly.io)

1. **Install Fly CLI** and login

2. **Deploy:**
   ```bash
   fly deploy
   ```

3. **Set secrets:**
   ```bash
   fly secrets set MONGO_URI="your_mongodb_connection_string"
   fly secrets set OPENROUTER_API_KEY="your_openrouter_api_key"
   fly secrets set FORGE_AI_API_KEY="your_api_key"
   ```

## API Endpoints

### POST /api/synthesize
Process team conversations and generate synthesis + individual briefings.

**Request:**
```json
{
  "forge_id": "abc123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Synthesis completed successfully",
  "synthesis_id": "1234567890"
}
```

### POST /api/chat
Handle chat messages and questions from team members.

**Request:**
```json
{
  "forge_id": "abc123",
  "role_id": "1",
  "message": "What should I focus on first?",
  "is_question": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Chat message processed successfully",
  "ai_response": "Based on your briefing, I'd suggest starting with..."
}
```

## Authentication

All endpoints require an API key in the Authorization header:
```
Authorization: Bearer your_api_key
``` 