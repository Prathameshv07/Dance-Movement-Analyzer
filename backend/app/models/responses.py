"""
Response models for API
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    models_loaded: bool
    models_ready: bool
    timestamp: str
    active_sessions: int


class SessionInfo(BaseModel):
    """Session information"""
    session_id: str
    filename: str
    status: str
    upload_time: str


class SessionListResponse(BaseModel):
    """List of sessions response"""
    success: bool
    count: int
    sessions: List[SessionInfo]


class ResultsResponse(BaseModel):
    """Analysis results response"""
    success: bool
    session_id: str
    status: str
    results: Optional[Dict[str, Any]] = None
    download_url: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    details: Optional[str] = None