# Forge AI Service API Documentation

The Forge AI Service provides a clean, production-ready API organized into logical groups for testing and managing AI prompts.

## 🏗️ API Organization

The API is organized into three main groups:

### 📊 **System Management** 
- `GET /` - Service information
- `GET /health` - Health check  
- `GET /status` - Detailed system status

### 🧪 **Prompt Testing**
- `GET /api/prompts` - List available prompts
- `GET /api/prompts/{name}` - Get prompt details  
- `GET /api/prompts/{name}/sample` - Get sample variables
- `POST /api/prompts/{name}/test` - Execute prompt test

### 🔗 **Webhook Processing**
- `POST /api/webhook/process-contribution` - Process contributions (authenticated)
- `GET /api/webhook/health` - Webhook health check

## 🚀 Quick Start

1. **Initialize prompts**:
   ```bash
   make seed-prompts-force
   ```

2. **Start the service**:
   ```bash
   make backend-dev
   ```

3. **Test the API**:
   ```bash
   make test-prompts
   ```

4. **View interactive docs**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 🧪 Prompt Testing Workflow

### Step 1: Discover Available Prompts
```bash
curl http://localhost:8000/api/prompts
```

**Response:**
```json
{
  "prompts": [
    {
      "name": "contribution_triage_agent",
      "version": 1,
      "description": "Analyzes user contributions to decide AI actions",
      "expected_vars": ["goal", "latest_contribution_text"],
      "parameters": {
        "model": "openrouter/google/gemini-2.5-flash-lite",
        "temperature": 0.1,
        "max_tokens": 100
      }
    }
  ],
  "total_count": 3
}
```

### Step 2: Get Prompt Details & Sample Data
```bash
curl http://localhost:8000/api/prompts/contribution_triage_agent
```

**Response:**
```json
{
  "prompt": {...},
  "template_preview": "You are a triage agent for a collaboration tool...",
  "sample_variables": {
    "goal": "Build a mobile app for task management",
    "latest_contribution_text": "I think we should use React Native..."
  }
}
```

### Step 3: Execute Prompt Test
```bash
curl -X POST http://localhost:8000/api/prompts/contribution_triage_agent/test \
  -H "Content-Type: application/json" \
  -d '{
    "variables": {
      "goal": "Build a mobile app for task management",
      "latest_contribution_text": "I think we should use React Native"
    }
  }'
```

**Response:**
```json
{
  "prompt_name": "contribution_triage_agent",
  "prompt_version": 1,
  "rendered_prompt": "You are a triage agent...",
  "model_response": "{\"action\": \"SYNTHESIZE\"}",
  "execution_time_ms": 1247,
  "model_used": "openrouter/google/gemini-2.5-flash-lite",
  "tokens_used": 95
}
```

## 🤖 Available AI Prompts

After running `make seed-prompts-force`, you'll have these Gemini-powered prompts:

### 1. **Contribution Triage Agent**
- **Model**: `gemini-2.5-flash-lite` (fast, cost-effective)
- **Purpose**: Analyze contributions and decide AI actions
- **Variables**: `goal`, `latest_contribution_text`
- **Output**: JSON with triage decision

### 2. **Direct Response Agent**  
- **Model**: `gemini-2.5-flash` (comprehensive)
- **Purpose**: Contextual responses to team questions
- **Variables**: `role`, `current_briefing`, `synthesis`, `chat_history_text`
- **Output**: Plain text response

### 3. **Synthesis Facilitator**
- **Model**: `gemini-2.5-flash` (comprehensive)
- **Purpose**: Generate briefing packages with individual insights
- **Variables**: `goal`, `roles_text`, `contributions_text`
- **Output**: JSON with overall context and individual briefings

## 📊 System Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Detailed Status
```bash
curl http://localhost:8000/status
```

Get comprehensive information about:
- Service version and environment
- Database connectivity
- Active prompts count
- AI model configuration
- Feature availability

## 🔧 Development Commands

```bash
# Seed/update prompts
make seed-prompts-force

# Start development server
make backend-dev

# Test all API endpoints
make test-prompts

# View help
make help
```

## 🛡️ Authentication

- **System endpoints**: No authentication required
- **Prompt testing**: No authentication required  
- **Webhook endpoints**: Bearer token required

## 📚 Interactive Documentation

The service automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
  - Try endpoints directly in the browser
  - See request/response schemas
  - Authentication testing

- **ReDoc**: http://localhost:8000/redoc  
  - Clean, professional documentation
  - Perfect for sharing with team members

## 🏷️ FastAPI Best Practices

This API follows FastAPI best practices:

✅ **Organized router groups** with logical prefixes  
✅ **Comprehensive documentation** with examples  
✅ **Proper HTTP status codes** and error handling  
✅ **Type-safe request/response models**  
✅ **Query parameter validation** with descriptions  
✅ **Automatic OpenAPI schema generation**  
✅ **Dependency injection** for services  
✅ **Background task processing** for performance  

## 🎯 Production Ready

This API is production-ready with:

- Comprehensive error handling and validation
- Structured logging with correlation IDs
- Performance monitoring (execution time, tokens)
- Database connection management
- Graceful startup/shutdown lifecycle
- CORS configuration 