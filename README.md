# Forge Project

Modern AI-powered collaboration platform with FastAPI backend and SvelteKit frontend.

## 🚀 Quick Start

```bash
# Complete setup (install everything + seed database)
make setup

# Start development (both frontend and backend)
make dev
```

## 📋 Essential Commands

### Setup & Installation
```bash
make setup          # Full project setup (install everything)
make install        # Install all dependencies  
make clean          # Clean all dependencies and artifacts
```

### Development
```bash
make dev            # Start both frontend and backend in dev mode
make backend        # Start backend only (Python FastAPI)
make frontend       # Start frontend only (SvelteKit)
```

### Testing & Quality
```bash
make test           # Run all tests (30 backend tests)
make lint           # Run linting for both frontend and backend
```

### Backend Utilities
```bash
make seed-prompts       # Initialize AI prompts in database
make generate-schemas   # Generate JSON schemas from Pydantic models
```

### Project Info
```bash
make status         # Show project status and dependencies
make help           # Show all available commands
```

## 🏗️ Architecture

- **Backend**: Python 3.13 + FastAPI + MongoDB (AI service with dynamic prompts)
- **Frontend**: SvelteKit + TypeScript (BFF pattern) 
- **AI**: Database-driven prompts with configurable models per task
- **Communication**: Webhook-based async processing with polling updates

## 💡 Key Features

- **Dynamic AI Configuration**: All model parameters stored in MongoDB, no hardcoded values
- **Production Ready**: Comprehensive testing, proper error handling, structured logging
- **Modern Tooling**: `uv` for Python dependencies, `make` for task orchestration
- **Type Safety**: Pydantic v2 models with automatic JSON schema generation

---

*Run `make help` to see all available commands*
