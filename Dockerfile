# Multi-stage Dockerfile for Dance Movement Analyzer
# Optimized for Hugging Face Spaces with MediaPipe model pre-download

# Stage 1: Base image with dependencies
FROM python:3.10-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
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

# Stage 2: Dependencies installation
FROM base as dependencies

# Copy requirements first for better caching
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download ALL MediaPipe models (as root before user switch)
# This downloads the models to the pip packages directory
RUN python3 -c "\
import mediapipe as mp; \
print('Downloading MediaPipe Pose models...'); \
# Model complexity 0 (Lite) \
pose0 = mp.solutions.pose.Pose(model_complexity=0, min_detection_confidence=0.5); \
pose0.close(); \
print('✅ Lite model downloaded'); \
# Model complexity 1 (Full) \
pose1 = mp.solutions.pose.Pose(model_complexity=1, min_detection_confidence=0.5); \
pose1.close(); \
print('✅ Full model downloaded'); \
# Model complexity 2 (Heavy) \
pose2 = mp.solutions.pose.Pose(model_complexity=2, min_detection_confidence=0.5); \
pose2.close(); \
print('✅ Heavy model downloaded'); \
print('✅ All MediaPipe models pre-downloaded successfully'); \
"

# Stage 3: Production image
FROM base as production

# Copy installed packages from dependencies stage (includes downloaded models)
COPY --from=dependencies /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Create necessary directories
RUN mkdir -p /app/uploads /app/outputs /app/logs

# Copy backend application
COPY backend/app /app/app

# Copy frontend files
COPY frontend /app/frontend

# Copy startup script
COPY startup.sh /app/startup.sh

# Make startup script executable
RUN chmod +x /app/startup.sh

# Set permissions for all app files
RUN chmod -R 755 /app

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose ports (7860 for Hugging Face, 8000 for local)
EXPOSE 8000
EXPOSE 7860

# Health check with 5 minute startup period
HEALTHCHECK --interval=30s --timeout=10s --start-period=5m --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run the application using startup script
CMD ["/app/startup.sh"]