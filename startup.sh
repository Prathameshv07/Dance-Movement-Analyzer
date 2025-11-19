#!/bin/bash
echo "🚀 Starting DanceDynamics..."
PORT=${PORT:-7860}
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1