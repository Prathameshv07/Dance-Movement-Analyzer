#!/bin/bash
set -e

echo "🚀 Starting Dance Movement Analyzer..."

# Verify MediaPipe models are available
echo "📦 Verifying MediaPipe models..."
python3 -c "
import mediapipe as mp
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Quick verification that models are accessible
    logger.info('Checking MediaPipe installation...')
    
    # Verify model files exist
    model_path = '/usr/local/lib/python3.10/site-packages/mediapipe/modules/pose_landmark'
    if os.path.exists(model_path):
        logger.info(f'✅ Model directory found: {model_path}')
        model_files = os.listdir(model_path)
        logger.info(f'Available models: {len(model_files)} files')
    else:
        logger.warning('⚠️ Model directory not found, models will load on first use')
    
    logger.info('✅ MediaPipe ready')
    
except Exception as e:
    logger.error(f'❌ Error verifying models: {e}')
    # Continue anyway - application will handle it
"

# Detect port (Hugging Face uses 7860, local uses 8000)
PORT=${PORT:-8000}

echo "🎬 Starting Uvicorn server on port $PORT..."
echo "📍 Application will be available at http://0.0.0.0:$PORT"
echo ""

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1 --log-level info