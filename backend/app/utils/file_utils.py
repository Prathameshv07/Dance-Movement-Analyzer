"""
File handling utilities
"""

import os
import uuid
from pathlib import Path
from typing import Dict, List

def generate_session_id() -> str:
    """Generate unique session ID for tracking"""
    return str(uuid.uuid4())


def validate_file_extension(filename: str, allowed_extensions: List[str] = [".mp4", ".avi", ".mov", ".mkv", ".webm"]) -> Dict:
    """
    Validate if file has allowed extension
    
    Args:
        filename: Name of the file
        allowed_extensions: List of allowed extensions (e.g., ['.mp4', '.avi'])
    
    Returns:
        Dict with valid status and error message
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


def cleanup_old_files(directory: Path, max_age_hours: int = 24):
    """
    Clean up files older than specified hours
    
    Args:
        directory: Directory to clean
        max_age_hours: Maximum file age in hours
    """
    import time
    import logging
    
    logger = logging.getLogger(__name__)
    
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