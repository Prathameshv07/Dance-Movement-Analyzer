"""
Utility functions for Dance Movement Analyzer
Provides helper functions for validation, logging, and common operations
"""

import os
import uuid
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from functools import wraps
from typing import List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_session_id() -> str:
    """Generate unique session ID for tracking"""
    return str(uuid.uuid4())


def validate_file_extension(filename: str, allowed_extensions: List[str] = [".mp4", ".avi", ".mov", ".mkv", ".webm"]) -> bool:
    """
    Validate if file has allowed extension
    
    Args:
        filename: Name of the file
        allowed_extensions: List of allowed extensions (e.g., ['.mp4', '.avi'])
    
    Returns:
        True if valid, False otherwise
    """
    
    ext = Path(filename).suffix.lower()
    if ext in allowed_extensions:
        return {"valid": True, "error": ""}
    else:
        return {"valid": False, "error": f"Invalid file extension: {ext}. Allowed extensions are {', '.join(allowed_extensions)}."}


def validate_file_size(file_path: Path, max_size_bytes: int) -> bool:
    """
    Validate if file size is within limit
    
    Args:
        file_path: Path to the file
        max_size_bytes: Maximum allowed size in bytes
    
    Returns:
        True if valid, False otherwise
    """
    if not file_path.exists():
        return False
    return file_path.stat().st_size <= max_size_bytes


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format
    
    Args:
        size_bytes: Size in bytes
    
    Returns:
        Formatted string (e.g., "10.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def timing_decorator(func):
    """
    Decorator to measure function execution time
    Useful for performance monitoring
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


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is zero
    
    Args:
        numerator: Number to divide
        denominator: Number to divide by
        default: Default value if division by zero
    
    Returns:
        Result of division or default value
    """
    return numerator / denominator if denominator != 0 else default


def create_success_response(data: Any, message: str = "Success") -> Dict[str, Any]:
    """
    Create standardized success response
    
    Args:
        data: Response data
        message: Success message
    
    Returns:
        Formatted response dictionary
    """
    return {
        "status": "success",
        "message": message,
        "data": data
    }


def create_error_response(error: str, details: Optional[str] = None) -> Dict[str, Any]:
    """
    Create standardized error response
    
    Args:
        error: Error message
        details: Additional error details
    
    Returns:
        Formatted error dictionary
    """
    response = {
        "status": "error",
        "error": error
    }
    if details:
        response["details"] = details
    return response


def cleanup_old_files(directory: Path, max_age_hours: int = 24):
    """
    Clean up files older than specified hours
    Useful for managing temporary upload/output files
    
    Args:
        directory: Directory to clean
        max_age_hours: Maximum file age in hours
    """
    if not directory.exists():
        return
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    for file_path in directory.iterdir():
        if file_path.is_file():
            file_age = current_time - file_path.stat().st_mtime
            if file_age > max_age_seconds:
                try:
                    file_path.unlink()
                    logger.info(f"Deleted old file: {file_path.name}")
                except Exception as e:
                    logger.error(f"Error deleting {file_path.name}: {e}")


def calculate_percentage(part: float, whole: float) -> float:
    """
    Calculate percentage with safe division
    
    Args:
        part: Part value
        whole: Whole value
    
    Returns:
        Percentage (0-100)
    """
    return safe_divide(part * 100, whole, 0.0)