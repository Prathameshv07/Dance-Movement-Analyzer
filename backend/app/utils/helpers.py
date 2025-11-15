"""
General helper functions
"""

import time
import logging
from functools import wraps
from typing import Any, Dict, Optional
import numpy as np

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

def convert_numpy_types(obj):
    """
    Recursively convert numpy types to native Python types for JSON serialization
    """
    if isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, (np.int_, np.intc, np.intp, np.int8, np.int16, np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj