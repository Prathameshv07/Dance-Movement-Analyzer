"""
File cleanup service for managing storage
"""

import asyncio
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from app.config import Config
from app.services.session_manager import session_manager

logger = logging.getLogger(__name__)


class CleanupService:
    """Manages automatic file cleanup"""
    
    def __init__(
        self,
        max_file_age_hours: int = 24,
        cleanup_interval_minutes: int = 60,
        max_storage_gb: float = 10.0
    ):
        """
        Args:
            max_file_age_hours: Delete files older than this
            cleanup_interval_minutes: Run cleanup every N minutes
            max_storage_gb: Maximum storage allowed (GB)
        """
        self.max_file_age_hours = max_file_age_hours
        self.cleanup_interval = cleanup_interval_minutes * 60  # Convert to seconds
        self.max_storage_bytes = max_storage_gb * 1024 * 1024 * 1024
        self.cleanup_task: Optional[asyncio.Task] = None
        self.is_running = False
    
    async def start(self):
        """Start background cleanup task"""
        if self.is_running:
            logger.warning("Cleanup service already running")
            return
        
        self.is_running = True
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info(f"✅ Cleanup service started (interval: {self.cleanup_interval/60:.0f}min)")
    
    async def stop(self):
        """Stop background cleanup task"""
        self.is_running = False
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 Cleanup service stopped")
    
    async def _cleanup_loop(self):
        """Background loop for periodic cleanup"""
        while self.is_running:
            try:
                await self.run_cleanup()
                await asyncio.sleep(self.cleanup_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
                await asyncio.sleep(60)  # Wait 1 min before retry
    
    async def run_cleanup(self):
        """Run cleanup operation"""
        logger.info("🧹 Starting cleanup operation...")
        
        # Cleanup old files
        deleted_by_age = await self._cleanup_old_files()
        
        # Cleanup by storage limit
        deleted_by_size = await self._cleanup_by_storage_limit()
        
        # Cleanup orphaned sessions
        cleaned_sessions = await self._cleanup_orphaned_sessions()
        
        total = deleted_by_age + deleted_by_size
        logger.info(
            f"✅ Cleanup complete: {total} files deleted, "
            f"{cleaned_sessions} sessions cleaned"
        )
        
        return {
            "deleted_by_age": deleted_by_age,
            "deleted_by_size": deleted_by_size,
            "cleaned_sessions": cleaned_sessions,
            "total_deleted": total
        }
    
    async def _cleanup_old_files(self) -> int:
        """Delete files older than max_file_age_hours"""
        deleted_count = 0
        cutoff_time = datetime.now() - timedelta(hours=self.max_file_age_hours)
        
        for folder in [Config.UPLOAD_FOLDER, Config.OUTPUT_FOLDER]:
            if not folder.exists():
                continue
            
            for file_path in folder.iterdir():
                if not file_path.is_file():
                    continue
                
                # Check file age
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                if file_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(f"🗑️  Deleted old file: {file_path.name}")
                    except Exception as e:
                        logger.error(f"Failed to delete {file_path.name}: {e}")
        
        return deleted_count
    
    async def _cleanup_by_storage_limit(self) -> int:
        """Delete oldest files if storage exceeds limit"""
        deleted_count = 0
        
        # Calculate total storage
        total_size = 0
        file_list = []
        
        for folder in [Config.UPLOAD_FOLDER, Config.OUTPUT_FOLDER]:
            if not folder.exists():
                continue
            
            for file_path in folder.iterdir():
                if file_path.is_file():
                    size = file_path.stat().st_size
                    mtime = file_path.stat().st_mtime
                    total_size += size
                    file_list.append((file_path, size, mtime))
        
        # Check if over limit
        if total_size <= self.max_storage_bytes:
            return 0
        
        # Sort by modification time (oldest first)
        file_list.sort(key=lambda x: x[2])
        
        # Delete oldest files until under limit
        for file_path, size, _ in file_list:
            if total_size <= self.max_storage_bytes:
                break
            
            try:
                file_path.unlink()
                total_size -= size
                deleted_count += 1
                logger.info(f"🗑️  Deleted for storage: {file_path.name}")
            except Exception as e:
                logger.error(f"Failed to delete {file_path.name}: {e}")
        
        return deleted_count
    
    async def _cleanup_orphaned_sessions(self) -> int:
        """Remove sessions with missing files or old failed sessions"""
        cleaned_count = 0
        sessions_to_remove = []
        
        for session_id, session in session_manager.sessions.items():
            # Remove failed sessions older than 1 hour
            if session.get("status") == "failed":
                upload_time = datetime.fromisoformat(session["upload_time"])
                if datetime.now() - upload_time > timedelta(hours=1):
                    sessions_to_remove.append(session_id)
                    continue
            
            # Remove sessions with missing files
            upload_path = session.get("upload_path")
            if upload_path and not Path(upload_path).exists():
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            session_manager.delete_session(session_id)
            cleaned_count += 1
            logger.info(f"🗑️  Cleaned orphaned session: {session_id}")
        
        return cleaned_count
    
    def get_storage_stats(self) -> dict:
        """Get current storage statistics"""
        total_size = 0
        file_count = 0
        
        for folder in [Config.UPLOAD_FOLDER, Config.OUTPUT_FOLDER]:
            if not folder.exists():
                continue
            
            for file_path in folder.iterdir():
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
        
        return {
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "total_size_gb": total_size / (1024 * 1024 * 1024),
            "file_count": file_count,
            "max_storage_gb": self.max_storage_bytes / (1024 * 1024 * 1024),
            "usage_percentage": (total_size / self.max_storage_bytes) * 100
        }


# Global cleanup service instance
cleanup_service = CleanupService(
    max_file_age_hours=24,
    cleanup_interval_minutes=60,
    max_storage_gb=10.0
)