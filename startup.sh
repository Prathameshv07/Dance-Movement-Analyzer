#!/bin/bash
set -e

echo "🚀 Starting Dance Movement Analyzer..."

# Pre-warm MediaPipe models
echo "📦 Pre-loading MediaPipe models..."
python3 -c "
import mediapipe as mp
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    logger.info('Loading Pose model...')
    pose = mp.solutions.pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    pose.close()
    logger.info('✅ Models loaded successfully')
except Exception as e:
    logger.error(f'❌ Error loading models: {e}')
    # Continue anyway - models will load on first use
" || echo "⚠️ Model pre-loading failed, will load on first use"

# Detect port (Hugging Face uses 7860, local uses 8000)
PORT=${PORT:-8000}

# Start the application
echo "🎬 Starting Uvicorn server on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
