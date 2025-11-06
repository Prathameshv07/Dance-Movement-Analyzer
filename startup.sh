#!/bin/bash
set -e

echo "🚀 Starting Dance Movement Analyzer..."
echo "📦 MediaPipe models pre-downloaded during build"

# ===============================
# Start Redis
# ===============================
echo "🧠 Starting Redis server..."
# redis-server --daemonize yes --bind 127.0.0.1 --port 6379 --requirepass "" 2>&1 | grep -v "Warning"

# Start Redis and check for failure
if ! redis-server --daemonize yes --bind 127.0.0.1 --port 6379 --requirepass "" 2>&1 | grep -v "Warning"; then
    echo "❌ Redis failed to start"
    exit 1
fi

# Wait for Redis
sleep 2

# Verify Redis
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis started on localhost:6379"
else
    echo "❌ Redis failed to start"
    exit 1
fi

# ===============================
# Start Celery Worker in Background
# ===============================
echo "⚙️ Starting Celery worker..."

# Start Celery with proper logging
celery -A app.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --max-tasks-per-child=10 \
    --time-limit=600 \
    --soft-time-limit=540 \
    > /tmp/celery.log 2>&1 &

CELERY_PID=$!

# Wait for Celery to start
sleep 3

# Check if Celery is running
if kill -0 $CELERY_PID 2>/dev/null; then
    echo "✅ Celery worker started (PID: $CELERY_PID)"
else
    echo "❌ Celery worker failed to start"
    echo "Celery logs:"
    cat /tmp/celery.log
    exit 1
fi

# ===============================
# Start Uvicorn (FastAPI)
# ===============================
PORT=${PORT:-7860}

echo "🎬 Starting Uvicorn server on port $PORT..."
echo "📍 Application will be available at http://0.0.0.0:$PORT soon"
echo ""

# Start Uvicorn
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --workers 1 \
    --log-level info \
    --access-log