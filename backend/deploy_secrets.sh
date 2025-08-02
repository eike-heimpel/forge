#!/bin/bash

# Deploy secrets to Fly.io from .env file
echo "🚀 Setting Fly.io secrets from .env file..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    exit 1
fi

# Source the .env file
set -a
source .env
set +a

# Set secrets in Fly.io
echo "📝 Setting MONGO_URI..."
fly secrets set MONGO_URI="$MONGO_URI"

echo "📝 Setting OPENROUTER_API_KEY..."
fly secrets set OPENROUTER_API_KEY="$OPENROUTER_API_KEY"

echo "📝 Setting OPENROUTER_MODEL..."
fly secrets set OPENROUTER_MODEL="$OPENROUTER_MODEL"

echo "📝 Setting FORGE_AI_API_KEY..."
fly secrets set FORGE_AI_API_KEY="$FORGE_AI_API_KEY"

echo "📝 Setting LOG_LEVEL..."
fly secrets set LOG_LEVEL="$LOG_LEVEL"

echo "✅ All secrets have been set!"
echo ""
echo "🔍 Verifying secrets list:"
fly secrets list

echo ""
echo "🚀 You can now deploy with: fly deploy" 