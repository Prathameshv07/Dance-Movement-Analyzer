#!/bin/bash
set -e

echo "🚀 Starting DanceDynamics on Hugging Face Spaces..."

# Get port from environment or use default
PORT=${PORT:-7860}

echo "📍 Port: $PORT"
echo "📂 Working Directory: $(pwd)"
echo "📁 Contents:"
ls -la

# Check if required directories exist
echo ""
echo "🔍 Checking structure..."
if [ -d "/app/frontend" ]; then
    echo "✅ Frontend directory found"
    ls -la /app/frontend | head -5
else
    echo "⚠️ Frontend directory not found at /app/frontend"
fi

if [ -d "/app/app" ]; then
    echo "✅ App directory found"
else
    echo "⚠️ App directory not found at /app/app"
fi

# Create necessary directories
echo ""
echo "📁 Creating upload/output directories..."
mkdir -p /app/uploads /app/outputs /app/logs
chmod 755 /app/uploads /app/outputs /app/logs

# Check Python environment
echo ""
echo "🐍 Python environment:"
python --version
echo "📦 Installed packages (key ones):"
pip list | grep -E "(fastapi|uvicorn|mediapipe|opencv)"

# Start the application
echo ""
echo "🎬 Starting FastAPI server..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --workers 1 \
    --log-level info \
    --access-log \
    --timeout-keep-alive 30 \
    --no-use-colors