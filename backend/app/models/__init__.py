"""
Data models for API requests and responses
"""

from .requests import (
    VideoUploadResponse,
    AnalysisStartRequest,
    AnalysisStartResponse
)

from .responses import (
    HealthResponse,
    SessionInfo,
    SessionListResponse,
    ResultsResponse,
    ErrorResponse
)

__all__ = [
    # Requests
    'VideoUploadResponse',
    'AnalysisStartRequest',
    'AnalysisStartResponse',
    
    # Responses
    'HealthResponse',
    'SessionInfo',
    'SessionListResponse',
    'ResultsResponse',
    'ErrorResponse'
]