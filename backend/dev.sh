#!/bin/bash

PORT="${PORT:-8000}"
HOST="${HOST:-0.0.0.0}"
ENV="${ENV:-dev}"

# Install dev dependencies if not already installed
if ! python -c "import ruff" 2>/dev/null; then
    echo "🚀 Installing development dependencies..."
    pip install -r requirements-dev.txt
fi

echo "🚀 Starting Simple FastAPI Test Server"
echo "🌍 Environment: $ENV"

echo "🌐 Host: $HOST"
echo "🔌 Port: $PORT"
echo "📖 Docs: http://$HOST:$PORT/docs"

uvicorn main:app --host 0.0.0.0 --port $PORT --forwarded-allow-ips '*' --reload
