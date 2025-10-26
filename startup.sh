#!/bin/bash
set -e

echo "🚀 Starting Dance Movement Analyzer..."
echo "📦 MediaPipe models pre-downloaded during build"

# Detect port (Hugging Face uses 7860, local uses 8000)
PORT=${PORT:-8000}

echo "🎬 Starting Uvicorn server on port $PORT..."
echo "📍 Application available at http://0.0.0.0:$PORT"
echo ""

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1 --log-level info