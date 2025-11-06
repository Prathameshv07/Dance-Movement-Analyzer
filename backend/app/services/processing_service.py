"""
Video processing service - Updated for Celery
"""

from app.tasks import process_video_task
from app.services.session_manager import session_manager
import logging

logger = logging.getLogger(__name__)


class ProcessingService:
    """Handles video processing tasks"""
    
    def start_processing(self, session_id: str) -> dict:
        """
        Start video processing with Celery
        
        Args:
            session_id: Session ID to process
            
        Returns:
            Dict with task info
        """
        try:
            # Submit task to Celery
            task = process_video_task.delay(session_id)
            
            # Update session with task ID
            session_manager.update_session(session_id, {
                "status": "queued",
                "celery_task_id": task.id
            })
            
            logger.info(f"✅ Task queued: {session_id} (task_id: {task.id})")
            
            return {
                "task_id": task.id,
                "status": "queued"
            }
            
        except Exception as e:
            logger.error(f"Failed to queue task: {e}")
            raise
    
    def get_task_status(self, task_id: str) -> dict:
        """Get Celery task status"""
        from celery.result import AsyncResult
        
        task = AsyncResult(task_id, app=process_video_task.app)
        
        if task.state == 'PENDING':
            response = {
                'state': task.state,
                'progress': 0,
                'message': 'Task pending...'
            }
        elif task.state == 'PROGRESS':
            response = {
                'state': task.state,
                'progress': task.info.get('progress', 0),
                'message': task.info.get('message', ''),
                'session_id': task.info.get('session_id', '')
            }
        elif task.state == 'SUCCESS':
            response = {
                'state': task.state,
                'progress': 1.0,
                'result': task.info
            }
        else:  # FAILURE, RETRY, etc.
            response = {
                'state': task.state,
                'progress': 0,
                'error': str(task.info)
            }
        
        return response


# Global processing service instance
processing_service = ProcessingService()