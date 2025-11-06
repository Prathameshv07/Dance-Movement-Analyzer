#!/bin/bash
set -e

echo "🚀 Starting Dance Movement Analyzer..."
echo "📦 MediaPipe models pre-downloaded during build"

# ===============================
# Start Redis in background
# ===============================
echo "🧠 Starting Redis server..."
redis-server --bind 127.0.0.1 --port 6379 --requirepass "" &
REDIS_PID=$!
sleep 3

if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis started on localhost:6379 (PID: $REDIS_PID)"
else
    echo "❌ Redis failed to start"
    exit 1
fi

# ===============================
# Start Celery Worker in Background
# ===============================
echo "⚙️ Starting Celery worker..."
celery -A app.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --max-tasks-per-child=10 \
    --time-limit=600 \
    --soft-time-limit=540 \
    > /tmp/celery.log 2>&1 &

CELERY_PID=$!
sleep 3

if kill -0 $CELERY_PID 2>/dev/null; then
    echo "✅ Celery worker started (PID: $CELERY_PID)"
else
    echo "❌ Celery worker failed to start"
    cat /tmp/celery.log
    exit 1
fi

# ===============================
# Start Uvicorn (FastAPI)
# ===============================
PORT=${PORT:-7860}

echo "🎬 Starting Uvicorn server on port $PORT..."
echo "📍 Application will be available at http://0.0.0.0:$PORT"
echo ""

exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --workers 1 \
    --log-level info