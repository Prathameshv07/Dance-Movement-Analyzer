"""
WebSocket connection management
"""

from typing import Dict
from fastapi import WebSocket
import logging
import json

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"✅ WebSocket connected: {session_id}")
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"🔌 WebSocket disconnected: {session_id}")
    
    async def send_message(self, session_id: str, message: dict):
        """Send JSON message to client"""
        if session_id in self.active_connections:
            try:
                # ✅ Ensure clean JSON serialization
                json_str = json.dumps(message, default=str)
                await self.active_connections[session_id].send_text(json_str)
                logger.debug(f"📤 Sent to {session_id}: {message.get('type')}")
            except Exception as e:
                logger.error(f"❌ Error sending to {session_id}: {e}")
                self.disconnect(session_id)
    
    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        disconnected = []
        for session_id, connection in self.active_connections.items():
            try:
                json_str = json.dumps(message, default=str)
                await connection.send_text(json_str)
            except Exception:
                disconnected.append(session_id)
        
        for session_id in disconnected:
            self.disconnect(session_id)


# Global manager instance
manager = ConnectionManager()