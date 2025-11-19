# ===============================
# Optimized for Hugging Face Spaces
# ===============================
FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# ===============================
# System dependencies (minimal)
# ===============================
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

# ===============================
# Verify FFmpeg
# ===============================
RUN ffmpeg -version 2>/dev/null || echo "⚠️ FFmpeg not found"

# ===============================
# Working directory
# ===============================
WORKDIR /app

# ===============================
# Python dependencies
# ===============================
COPY backend/requirements.txt .

# Install dependencies with retry logic
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt || \
    (echo "Retrying pip install..." && pip install --no-cache-dir -r requirements.txt)

# ===============================
# Pre-download MediaPipe models
# ===============================
RUN echo "📥 Downloading MediaPipe Pose models..." && \
    python3 -c "import mediapipe as mp; mp.solutions.pose.Pose(model_complexity=0).close(); print('✅ Models ready');" || \
    echo "⚠️ MediaPipe model download failed (will download on first use)"

# ===============================
# Copy application files
# ===============================
COPY backend/app /app/app
COPY frontend /app/frontend
COPY startup.sh /app/startup.sh

# ===============================
# Create directories and permissions
# ===============================
RUN mkdir -p /app/uploads /app/outputs /app/logs && \
    chmod +x /app/startup.sh && \
    chmod -R 755 /app

# ===============================
# Non-root user for security
# ===============================
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# ===============================
# Expose port
# ===============================
EXPOSE 7860

# ===============================
# Health check
# ===============================
HEALTHCHECK --interval=30s --timeout=10s --start-period=5m --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# ===============================
# Startup
# ===============================
CMD ["/bin/bash", "/app/startup.sh"]