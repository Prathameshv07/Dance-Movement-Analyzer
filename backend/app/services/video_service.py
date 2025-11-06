"""
Video handling service
"""

from pathlib import Path
from typing import Optional
import shutil
import logging

from app.config import Config
from app.utils.file_utils import validate_file_extension, format_file_size
from app.core.video_processor import VideoProcessor

logger = logging.getLogger(__name__)


class VideoService:
    """Handles video upload and validation"""
    
    def __init__(self):
        self.processor: Optional[VideoProcessor] = None
    
    def get_processor(self) -> VideoProcessor:
        """Get or create VideoProcessor instance"""
        if self.processor is None:
            logger.info("Initializing VideoProcessor...")
            self.processor = VideoProcessor()
            logger.info("✅ VideoProcessor initialized")
        return self.processor
    
    def validate_video(self, filename: str) -> dict:
        """Validate video file"""
        from typing import List
        allowed_extensions: List[str] = [".mp4", ".avi", ".mov", ".mkv", ".webm"]
        return validate_file_extension(filename, allowed_extensions)
    
    def save_upload(self, file, session_id: str, filename: str) -> Path:
        """Save uploaded file"""
        upload_path = Config.UPLOAD_FOLDER / f"{session_id}_{filename}"
        
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Saved upload: {upload_path.name}")
        return upload_path
    
    def load_video_info(self, upload_path: Path) -> dict:
        """Load video metadata"""
        processor = self.get_processor()
        video_info = processor.load_video(upload_path)
        
        return {
            "filename": upload_path.name,
            "size": format_file_size(video_info["size_bytes"]),
            "duration": f"{video_info['duration']:.1f}s",
            "resolution": f"{video_info['width']}x{video_info['height']}",
            "fps": video_info["fps"],
            "frame_count": video_info["frame_count"]
        }
    
    def cleanup_session_files(self, session: dict):
        """Delete session files"""
        try:
            if "upload_path" in session:
                Path(session["upload_path"]).unlink(missing_ok=True)
            if "output_path" in session:
                Path(session["output_path"]).unlink(missing_ok=True)
            if "results_path" in session:
                Path(session["results_path"]).unlink(missing_ok=True)
        except Exception as e:
            logger.error(f"Error deleting files: {e}")


# Global video service instance
video_service = VideoService()