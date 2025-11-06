"""
Celery application for background task processing
"""

from celery import Celery
import os

# Redis URL from environment or default
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "dance_analyzer",
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
    task_soft_time_limit=540,  # 9 minutes soft limit
    worker_prefetch_multiplier=1,  # Take one task at a time
    worker_max_tasks_per_child=10,  # Restart worker after 10 tasks
    imports=['app.tasks']  # ✅ IMPORTANT: Tell Celery where to find tasks
)

# Auto-discover tasks
celery_app.autodiscover_tasks(['app'])