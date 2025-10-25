"""
Configuration management for Dance Movement Analyzer
Centralizes all application settings and constants
"""

import os
from pathlib import Path
from typing import List

class Config:
    """Application configuration with environment variable support"""
    
    # Application Settings
    APP_NAME: str = "Dance Movement Analyzer"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # File Upload Settings
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: List[str] = [".mp4", ".avi", ".mov", ".mkv", ".webm"]
    UPLOAD_FOLDER: Path = Path("uploads")
    OUTPUT_FOLDER: Path = Path("outputs")
    
    # Video Processing Settings
    MAX_VIDEO_DURATION: int = 60  # seconds
    TARGET_FPS: int = 30
    FRAME_SKIP: int = 1  # Process every Nth frame (1 = no skip)
    
    # MediaPipe Configuration
    MEDIAPIPE_MODEL_COMPLEXITY: int = 1  # 0=Lite, 1=Full, 2=Heavy
    MEDIAPIPE_MIN_DETECTION_CONFIDENCE: float = 0.5
    MEDIAPIPE_MIN_TRACKING_CONFIDENCE: float = 0.5
    MEDIAPIPE_SMOOTH_LANDMARKS: bool = True
    
    # Skeleton Overlay Settings
    SKELETON_LINE_THICKNESS: int = 2
    SKELETON_CIRCLE_RADIUS: int = 4
    SKELETON_COLOR: tuple = (0, 255, 0)  # Green in BGR
    SKELETON_CONFIDENCE_THRESHOLD: float = 0.5
    
    # Movement Classification Thresholds
    MOVEMENT_INTENSITY_LOW: float = 0.02
    MOVEMENT_INTENSITY_MEDIUM: float = 0.05
    MOVEMENT_INTENSITY_HIGH: float = 0.10
    
    # Movement velocity thresholds (normalized units)
    VELOCITY_STANDING: float = 0.01
    VELOCITY_WALKING: float = 0.03
    VELOCITY_DANCING: float = 0.06
    VELOCITY_JUMPING: float = 0.12
    
    # API Settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    CORS_ORIGINS: List[str] = ["*"]
    
    @classmethod
    def initialize_folders(cls):
        """Create necessary folders if they don't exist"""
        cls.UPLOAD_FOLDER.mkdir(exist_ok=True)
        cls.OUTPUT_FOLDER.mkdir(exist_ok=True)
    
    @classmethod
    def get_mediapipe_config(cls) -> dict:
        """Get MediaPipe Pose configuration as dictionary"""
        return {
            "model_complexity": cls.MEDIAPIPE_MODEL_COMPLEXITY,
            "min_detection_confidence": cls.MEDIAPIPE_MIN_DETECTION_CONFIDENCE,
            "min_tracking_confidence": cls.MEDIAPIPE_MIN_TRACKING_CONFIDENCE,
            "smooth_landmarks": cls.MEDIAPIPE_SMOOTH_LANDMARKS
        }