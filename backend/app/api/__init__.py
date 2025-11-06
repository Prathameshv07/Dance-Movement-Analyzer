"""
API layer - routes and websocket handling
"""

from .routes import router
from .websocket import manager, ConnectionManager
from .dependencies import get_video_processor

__all__ = [
    'router',
    'manager',
    'ConnectionManager',
    'get_video_processor'
]