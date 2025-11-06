"""
Shared API dependencies
"""

from typing import Optional
from app.core.video_processor import VideoProcessor

# Global processor instance
global_processor: Optional[VideoProcessor] = None


def get_video_processor() -> VideoProcessor:
    """Get or create the global VideoProcessor instance"""
    global global_processor
    if global_processor is None:
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Initializing VideoProcessor (first use)...")
        global_processor = VideoProcessor()
        logger.info("✅ VideoProcessor initialized")
    return global_processor