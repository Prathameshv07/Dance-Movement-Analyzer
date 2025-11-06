"""
Request models for API validation
"""

from typing import Optional
from pydantic import BaseModel, Field


class VideoUploadResponse(BaseModel):
    """Response model for video upload"""
    success: bool
    session_id: str
    filename: str
    size: str
    duration: str
    resolution: str
    fps: float
    frame_count: int


class AnalysisStartRequest(BaseModel):
    """Request model to start analysis"""
    session_id: str = Field(..., description="Session ID from upload")


class AnalysisStartResponse(BaseModel):
    """Response model for analysis start"""
    success: bool
    message: str
    session_id: str
    websocket_url: str