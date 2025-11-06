#!/bin/bash
set -e

echo "🚀 Starting Dance Movement Analyzer..."
echo "📦 MediaPipe models pre-downloaded during build"

# Detect port (Hugging Face uses 7860, local uses 8000)
PORT=${PORT:-7860}

# -----------------------------
# Start Redis (non-root friendly)
# -----------------------------
echo "🧠 Starting Redis server..."
redis-server --daemonize yes
sleep 2  # give Redis a moment to start
echo "✅ Redis started on localhost:6379"

# -----------------------------
# Start Celery worker
# -----------------------------
echo "⚙️ Starting Celery worker..."
celery -A app.celery_app worker --loglevel=info &
sleep 2

# -----------------------------
# Start FastAPI (Uvicorn)
# -----------------------------
echo "🎬 Starting Uvicorn server on port $PORT..."
echo "📍 Application will available at http://0.0.0.0:$PORT soon"
echo ""

exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --workers 1 --log-level info

