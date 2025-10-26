# Multi-stage Dockerfile for Dance Movement Analyzer
# Optimized for Hugging Face Spaces

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

# Pre-download MediaPipe models to speed up first run
RUN python -c "import mediapipe as mp; pose = mp.solutions.pose.Pose(); pose.close()" || true

# Stage 3: Production image
FROM base as production

# Copy installed packages from dependencies stage
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

# Set permissions
RUN chmod -R 755 /app

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose port (7860 for Hugging Face, 8000 for local)
EXPOSE 8000
EXPOSE 7860

# ⬇️ OPTION B: HEALTHCHECK GOES HERE ⬇️
# Health check with 5 minute startup period (for model loading)
# This allows the container up to 5 minutes to start before health checks begin
HEALTHCHECK --interval=30s --timeout=10s --start-period=5m --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1
# ⬆️ HEALTHCHECK ENDS HERE ⬆️

# Run the application using startup script
CMD ["/app/startup.sh"]