"""
Celery background tasks
"""

from pathlib import Path
from datetime import datetime
import json
import logging

from app.celery_app import celery_app
from app.config import Config
from app.core.video_processor import VideoProcessor
from app.services.session_manager import session_manager

logger = logging.getLogger(__name__)


def convert_to_native_bool(obj):
    """Convert numpy types to native Python types"""
    import numpy as np
    if isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    elif isinstance(obj, dict):
        return {k: convert_to_native_bool(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_native_bool(v) for v in obj]
    else:
        return obj


@celery_app.task(bind=True, name='process_video_task')
def process_video_task(self, session_id: str):
    """
    Celery task for video processing
    
    Args:
        self: Celery task instance
        session_id: Session ID to process
    """
    try:
        logger.info(f"🎬 Starting processing for session: {session_id}")
        
        # Get session (need to recreate session_manager in worker)
        # In production, you'd fetch from Redis/DB
        session = session_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        input_path = Path(session["upload_path"])
        output_path = Config.OUTPUT_FOLDER / f"analyzed_{session_id}.mp4"
        results_path = Config.OUTPUT_FOLDER / f"results_{session_id}.json"
        
        # Update session status
        session_manager.update_session(session_id, {
            "status": "processing",
            "celery_task_id": self.request.id
        })
        
        # Create processor
        processor = VideoProcessor()
        
        # Progress callback (updates Celery task state)
        def progress_callback(progress: float, message: str):
            self.update_state(
                state='PROGRESS',
                meta={
                    'progress': progress,
                    'message': message,
                    'session_id': session_id
                }
            )
            logger.info(f"Progress {session_id}: {progress*100:.1f}% - {message}")
        
        # Process video
        logger.info(f"Processing video: {input_path}")
        raw_results = processor.process_video(
            video_path=input_path,
            output_path=output_path,
            progress_callback=progress_callback
        )
        
        # Convert results
        results = convert_to_native_bool(raw_results)
        
        # Save JSON
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Update session
        session_manager.update_session(session_id, {
            "status": "completed",
            "output_path": str(output_path),
            "results_path": str(results_path),
            "end_time": datetime.now().isoformat(),
            "results": results
        })
        
        logger.info(f"✅ Processing completed: {session_id}")
        
        return {
            "status": "completed",
            "session_id": session_id,
            "results": results,
            "output_path": str(output_path)
        }
        
    except Exception as e:
        logger.error(f"❌ Processing failed for {session_id}: {str(e)}")
        
        session_manager.update_session(session_id, {
            "status": "failed",
            "error": str(e)
        })
        
        raise  # Re-raise for Celery to mark as failed