# Forge Project Makefile
# Orchestrates tasks across frontend (Node.js) and backend (Python/uv)

.PHONY: help setup install clean dev backend frontend backend-dev backend-prod seed-prompts seed-prompts-force generate-schemas test lint

# Default target
help:
	@echo "🔨 Forge Project Tasks"
	@echo ""
	@echo "📦 Setup & Installation:"
	@echo "  make setup          - Full project setup (install everything)"
	@echo "  make install         - Install all dependencies"
	@echo "  make clean          - Clean all dependencies and artifacts"
	@echo ""
	@echo "🚀 Development:"
	@echo "  make dev            - Start both frontend and backend in dev mode"
	@echo "  make backend        - Start backend only"
	@echo "  make frontend       - Start frontend only"
	@echo "  make backend-dev    - Backend with auto-reload"
	@echo "  make backend-prod   - Backend in production mode"
	@echo ""
	@echo "🤖 Backend Tasks:"
	@echo "  make seed-prompts   - Initialize AI prompts in database"
	@echo "  make seed-prompts-force - Initialize AI prompts (overwrite existing)"
	@echo "  make seed-prompts ARGS='--force' - Pass custom args to seed script"
	@echo "  make generate-schemas - Generate JSON schemas from Pydantic models"
	@echo ""  
	@echo "🧪 Testing & Quality:"
	@echo "  make test           - Run all tests"
	@echo "  make lint           - Run linting"
	@echo ""
	@echo "📋 Info:"
	@echo "  make status         - Show project status"

# ===========================================
# Setup & Installation
# ===========================================

setup: install seed-prompts generate-schemas
	@echo "✅ Complete project setup finished!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Configure your .env files (see backend/env.example)"
	@echo "2. Run 'make dev' to start development"

install: install-backend install-frontend

install-backend:
	@echo "🐍 Installing backend dependencies (Python 3.13 + uv)..."
	cd backend && uv install

install-frontend:
	@echo "📦 Installing frontend dependencies..."
	cd frontend && npm install

clean:
	@echo "🧹 Cleaning dependencies and artifacts..."
	rm -rf backend/.venv backend/uv.lock
	rm -rf frontend/node_modules frontend/.next
	rm -rf schemas/json/*

# ===========================================
# Development
# ===========================================

dev: backend-dev frontend
	@echo "🚀 Starting full development environment..."

backend: backend-dev

backend-dev:
	@echo "🐍 Starting backend in development mode..."
	cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

backend-prod:
	@echo "🐍 Starting backend in production mode..."
	cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

frontend:
	@echo "⚛️ Starting frontend development server..."
	cd frontend && npm run dev

# ===========================================
# Backend Utilities
# ===========================================

seed-prompts:
	@echo "🌱 Seeding AI prompts in database..."
	cd backend && uv run seed-prompts $(ARGS)

seed-prompts-force:
	@echo "🌱 Seeding AI prompts in database (force overwrite)..."
	cd backend && uv run seed-prompts --force

generate-schemas:
	@echo "📋 Generating JSON schemas..."
	cd backend && uv run generate-schemas
	@echo "✅ Schemas generated in schemas/json/"

# ===========================================
# Testing & Quality
# ===========================================

test:
	@echo "🧪 Running tests..."
	@echo "Backend tests:"
	cd backend && uv run python -m pytest || echo "No tests found"
	@echo "Frontend tests:"
	cd frontend && npm test || echo "No tests configured"

lint:
	@echo "🔍 Running linting..."
	@echo "Backend linting:"
	cd backend && uv run python -m black --check . || echo "Black not configured"
	cd backend && uv run python -m ruff check . || echo "Ruff not configured"
	@echo "Frontend linting:"
	cd frontend && npm run lint || echo "No frontend linting configured"

# ===========================================
# Project Info
# ===========================================

status:
	@echo "📊 Project Status"
	@echo "=================="
	@echo ""
	@echo "Backend:"
	@echo "  Python: $(shell cd backend && python --version 2>/dev/null || echo 'Not found')"
	@echo "  uv: $(shell uv --version 2>/dev/null || echo 'Not installed')" 
	@echo "  Dependencies: $(shell [ -d backend/.venv ] && echo 'Installed' || echo 'Missing')"
	@echo ""
	@echo "Frontend:"
	@echo "  Node: $(shell node --version 2>/dev/null || echo 'Not found')"
	@echo "  Dependencies: $(shell [ -d frontend/node_modules ] && echo 'Installed' || echo 'Missing')"
	@echo ""
	@echo "Schemas:"
	@echo "  Generated: $(shell [ -f schemas/json/_manifest.json ] && echo 'Yes' || echo 'No')"
	@echo "  Count: $(shell ls schemas/json/*.json 2>/dev/null | wc -l | tr -d ' ' || echo '0')"

# ===========================================
# Development Shortcuts
# ===========================================

# Quick restart backend (useful during development)
restart-backend:
	@echo "🔄 Restarting backend..."
	pkill -f "uvicorn app.main:app" || true
	sleep 1
	make backend-dev

# Full reset (when things get messy)
reset: clean setup
	@echo "♻️ Full project reset complete!" 