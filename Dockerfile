# Optimized Dockerfile with full H.264 support
FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies with full ffmpeg and x264
RUN apt-get update && apt-get install -y --no-install-recommends \
    redis-tools \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    ffmpeg \
    libavcodec-extra \
    libx264-dev \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Verify FFmpeg has H.264 encoder
RUN ffmpeg -codecs 2>/dev/null | grep -i h264 || echo "H.264 codec not available, will use fallback"

WORKDIR /app

# Copy and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download MediaPipe models
RUN echo "Downloading MediaPipe Pose models..." && \
    python3 -c "import mediapipe as mp; \
    pose0 = mp.solutions.pose.Pose(model_complexity=0, min_detection_confidence=0.5); pose0.close(); \
    pose1 = mp.solutions.pose.Pose(model_complexity=1, min_detection_confidence=0.5); pose1.close(); \
    pose2 = mp.solutions.pose.Pose(model_complexity=2, min_detection_confidence=0.5); pose2.close(); \
    print('✅ All models pre-downloaded');" && \
    echo "MediaPipe models downloaded"

# Set permissions
RUN chmod -R 755 /usr/local/lib/python3.10/site-packages/mediapipe

# Create directories
RUN mkdir -p /app/uploads /app/outputs /app/logs

# Copy application
COPY backend/app /app/app
COPY frontend /app/frontend
COPY startup.sh /app/startup.sh
RUN chmod +x /app/startup.sh

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /usr/local/lib/python3.10/site-packages/mediapipe && \
    chown -R root:root /usr/local/lib/python3.10/site-packages/mediapipe

USER appuser

EXPOSE 7860 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5m --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:7860/health')" || exit 1

CMD ["/app/startup.sh"]