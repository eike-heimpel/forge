# Forge AI Backend

Production-ready FastAPI service implementing the **PoC Architecture** for AI-powered collaboration.

## 🏗️ Architecture

- **Webhook-based processing**: SvelteKit BFF → Python AI Service
- **Database-driven prompts**: All AI models & parameters stored in MongoDB
- **AI Triage System**: Fast decision → Targeted action (LOG_ONLY, ANSWER_DIRECTLY, SYNTHESIZE)
- **Async processing**: Fast webhook response + background AI work

## 🚀 Setup

### 1. Environment

```bash
cd backend
uv install  # Install Python 3.13 + dependencies
```

### 2. Configuration

Create `.env` file:

```bash
# Required
MONGO_URI=mongodb://localhost:27017/forge
OPENROUTER_API_KEY=your_openrouter_api_key
FORGE_AI_API_KEY=your_secure_webhook_key

# Optional
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 3. Database Setup

```bash
# Initialize database with AI prompts
uv run seed-prompts
```

This creates 3 prompts in MongoDB:
- `contribution_triage_agent` (fast triage decisions)  
- `direct_response_agent` (direct answers to questions)
- `synthesis_facilitator_default` (structured synthesis)

### 4. Run

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📊 Data Models

### MongoDB Collections

**`forges`** - Collaboration workspaces
**`contributions`** - Append-only activity log  
**`ai_prompts`** - Dynamic prompt + model configuration

Each prompt has:
```json
{
  "parameters": {
    "model": "provider/model-name",
    "temperature": 0.1,
    "max_tokens": 100,
    "response_format": { "type": "json_object" }
  }
}
```

## 🔗 API Endpoints

### Webhook (for SvelteKit BFF)
- `POST /api/webhook/process-contribution` - Process new contributions

### Health & Status
- `GET /health` - Service health
- `GET /api/status` - Detailed status
- `GET /webhook/health` - Webhook health

## 🛠️ Development

### Generate JSON Schemas
```bash
uv run generate-schemas
```
Creates schemas in `../schemas/json/` for frontend consumption.

### Database Management
```bash
# Seed initial prompts
uv run seed-prompts

# Re-run is safe (skips existing)
uv run seed-prompts
```

## 🔄 Workflow

1. **SvelteKit BFF** posts webhook: `{ forgeId, newContributionId }`
2. **Fast Response**: `202 Accepted` 
3. **Background AI**:
   - Triage: What action? (LOG_ONLY/ANSWER_DIRECTLY/SYNTHESIZE)
   - Action: Execute with prompt-specific model & parameters from database
   - Result: Save to database
4. **Frontend Polling**: Checks for updates

## 🎯 Benefits

- **Flexible**: Change AI models per prompt without code changes
- **Cost-efficient**: Use appropriate models for each task (fast for decisions, powerful for complex work)
- **Maintainable**: No hardcoded prompts or model configuration
- **Scalable**: Database-driven, async processing
- **Observable**: Structured logging throughout 