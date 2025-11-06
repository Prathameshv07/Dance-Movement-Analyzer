# app/tasks.py
from celery import shared_task
from app.celery_app import celery_app
from app.services.video_service import video_service
from app.services.session_manager import session_manager
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, name="process_video_task")
def process_video_task(self, session_id: str):
    """Celery task for video processing"""
    try:
        logger.info(f"🎥 Starting processing for session: {session_id}")
        session_manager.update_session(session_id, {"status": "processing"})

        result = video_service.process_video(session_id)

        session_manager.update_session(session_id, {"status": "completed", "result": result})
        logger.info(f"✅ Completed processing for session: {session_id}")
        return {"status": "completed", "result": result}

    except Exception as e:
        logger.error(f"❌ Processing failed for session {session_id}: {e}", exc_info=True)
        session_manager.update_session(session_id, {"status": "failed", "error": str(e)})
        raise e
