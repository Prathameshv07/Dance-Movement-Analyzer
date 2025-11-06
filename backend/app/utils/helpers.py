"""
General helper functions
"""

import time
import logging
from functools import wraps
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def timing_decorator(func):
    """
    Decorator to measure function execution time
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"{func.__name__} executed in {execution_time:.2f} seconds")
        return result
    return wrapper


def create_success_response(data: Any, message: str = "Success") -> Dict[str, Any]:
    """
    Create standardized success response
    """
    return {
        "status": "success",
        "message": message,
        "data": data
    }


def create_error_response(error: str, details: Optional[str] = None) -> Dict[str, Any]:
    """
    Create standardized error response
    """
    response = {
        "status": "error",
        "error": error
    }
    if details:
        response["details"] = details
    return response