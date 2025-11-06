"""
Session management service
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages processing sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_session(self, session_id: str, filename: str, upload_path: str, video_info: Dict) -> Dict[str, Any]:
        """Create a new session"""
        session = {
            "session_id": session_id,
            "filename": filename,
            "upload_path": upload_path,
            "upload_time": datetime.now().isoformat(),
            "status": "uploaded",
            "video_info": video_info,
            "results": None,
            "progress": 0.0,
            "message": ""
        }
        
        self.sessions[session_id] = session
        logger.info(f"Created session: {session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session data"""
        if session_id in self.sessions:
            self.sessions[session_id].update(updates)
            return True
        return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
            return True
        return False
    
    def list_sessions(self) -> list:
        """List all sessions"""
        return [
            {
                "session_id": sid,
                "filename": s["filename"],
                "status": s["status"],
                "upload_time": s["upload_time"]
            }
            for sid, s in self.sessions.items()
        ]
    
    def get_active_count(self) -> int:
        """Get count of active sessions"""
        return len(self.sessions)


# Global session manager instance
session_manager = SessionManager()