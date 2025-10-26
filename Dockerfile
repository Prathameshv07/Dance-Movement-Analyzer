# Optimized Dockerfile for Dance Movement Analyzer
# Fixes MediaPipe model permission issues

# FROM python:3.10-slim
FROM python:3.10

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    mesa-utils \
    libgl1 \
    # libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download MediaPipe models (as root, before creating non-root user)
RUN echo "Downloading MediaPipe Pose models..." && \
    python3 -c "import mediapipe as mp; \
    print('Downloading Lite model...'); \
    pose0 = mp.solutions.pose.Pose(model_complexity=0, min_detection_confidence=0.5); \
    pose0.close(); \
    print('✅ Lite model downloaded'); \
    print('Downloading Full model...'); \
    pose1 = mp.solutions.pose.Pose(model_complexity=1, min_detection_confidence=0.5); \
    pose1.close(); \
    print('✅ Full model downloaded'); \
    print('Downloading Heavy model...'); \
    pose2 = mp.solutions.pose.Pose(model_complexity=2, min_detection_confidence=0.5); \
    pose2.close(); \
    print('✅ Heavy model downloaded'); \
    print('✅ All models pre-downloaded successfully');" && \
    echo "MediaPipe models downloaded successfully"

# Set proper permissions for MediaPipe models directory
RUN chmod -R 755 /usr/local/lib/python3.10/site-packages/mediapipe

# Create necessary directories
RUN mkdir -p /app/uploads /app/outputs /app/logs

# Copy application files
COPY backend/app /app/app
COPY frontend /app/frontend

# Copy startup script
COPY startup.sh /app/startup.sh
RUN chmod +x /app/startup.sh

# Create non-root user
RUN useradd -m -u 1000 appuser

# Set ownership of app directory
RUN chown -R appuser:appuser /app

# IMPORTANT: Keep MediaPipe models readable by non-root user
RUN chmod -R 755 /usr/local/lib/python3.10/site-packages/mediapipe && \
    chown -R root:root /usr/local/lib/python3.10/site-packages/mediapipe

# Switch to non-root user
USER appuser

# Expose ports
EXPOSE 7860
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5m --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:7860/health')" || exit 1

# Start application
CMD ["/app/startup.sh"]