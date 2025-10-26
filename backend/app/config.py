"""
Configuration Management - Updated for Phase 3 & 4
Centralized configuration for the Dance Movement Analyzer
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from dataclasses import dataclass, field
from typing import Dict, Any

# Load environment variables
load_dotenv()


@dataclass
class Config:
    """Configuration management for the application"""
    
    # ==================== API Configuration ====================
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # CORS Settings
    # CORS_ORIGINS: list = os.getenv(
    #     "CORS_ORIGINS", 
    #     "*"  # In production, set to specific domains
    # ).split(",")
    CORS_ORIGINS: list = field(default_factory=lambda: os.getenv(
        "CORS_ORIGINS", "*"
    ).split(","))
    
    # ==================== File Configuration ====================
    # Base directories
    BASE_DIR: Path = Path(__file__).parent.parent
    UPLOAD_FOLDER: Path = BASE_DIR / "uploads"
    OUTPUT_FOLDER: Path = BASE_DIR / "outputs"
    SAMPLE_FOLDER: Path = BASE_DIR / "sample_videos"
    
    # File limits
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", 104857600))  # 100MB
    MAX_VIDEO_DURATION: int = int(os.getenv("MAX_VIDEO_DURATION", 60))  # seconds
    
    # Supported formats
    SUPPORTED_VIDEO_FORMATS: tuple = (".mp4", ".avi", ".mov", ".webm")
    SUPPORTED_MIME_TYPES: tuple = (
        "video/mp4",
        "video/avi",
        "video/quicktime",
        "video/webm"
    )
    
    # ==================== MediaPipe Configuration ====================
    # Model complexity: 0 (Lite), 1 (Full), 2 (Heavy)
    MEDIAPIPE_MODEL_COMPLEXITY: int = int(
        # os.getenv("MEDIAPIPE_MODEL_COMPLEXITY", 1)
        os.getenv("MEDIAPIPE_MODEL_COMPLEXITY", 0)
    )
    
    # Confidence thresholds
    MEDIAPIPE_MIN_DETECTION_CONFIDENCE: float = float(
        os.getenv("MEDIAPIPE_MIN_DETECTION_CONFIDENCE", 0.5)
    )
    MEDIAPIPE_MIN_TRACKING_CONFIDENCE: float = float(
        os.getenv("MEDIAPIPE_MIN_TRACKING_CONFIDENCE", 0.5)
    )
    
    # Smoothing
    MEDIAPIPE_SMOOTH_LANDMARKS: bool = os.getenv(
        "MEDIAPIPE_SMOOTH_LANDMARKS", "True"
    ).lower() == "true"
    
    # ==================== Processing Configuration ====================
    # Video processing
    TARGET_FPS: int = int(os.getenv("TARGET_FPS", 30))
    FRAME_SKIP: int = int(os.getenv("FRAME_SKIP", 1))  # Process every Nth frame
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", 30))  # Frames per batch
    
    # Output settings
    # OUTPUT_VIDEO_CODEC: str = os.getenv("OUTPUT_VIDEO_CODEC", "mp4v")
    OUTPUT_VIDEO_CODEC: str = os.getenv("OUTPUT_VIDEO_CODEC", "avc1")
    OUTPUT_VIDEO_FPS: int = int(os.getenv("OUTPUT_VIDEO_FPS", 30))
    OUTPUT_VIDEO_QUALITY: int = int(os.getenv("OUTPUT_VIDEO_QUALITY", 90))
    
    # ==================== Movement Classification ====================
    # Velocity thresholds (normalized units per frame)
    VELOCITY_STANDING: float = 0.01
    VELOCITY_WALKING: float = 0.03
    VELOCITY_DANCING: float = 0.06
    VELOCITY_JUMPING: float = 0.12
    
    # Intensity thresholds
    MOVEMENT_INTENSITY_LOW: float = 0.02
    MOVEMENT_INTENSITY_MEDIUM: float = 0.05
    MOVEMENT_INTENSITY_HIGH: float = 0.08
    
    # Smoothing window for movement analysis
    MOVEMENT_SMOOTHING_WINDOW: int = 5
    
    # ==================== Visualization Configuration ====================
    # Skeleton overlay settings
    SKELETON_COLOR_HIGH_CONF: tuple = (0, 255, 0)  # Green
    SKELETON_COLOR_MED_CONF: tuple = (0, 255, 255)  # Yellow
    SKELETON_COLOR_LOW_CONF: tuple = (0, 165, 255)  # Orange
    SKELETON_LINE_THICKNESS: int = 2
    SKELETON_CIRCLE_RADIUS: int = 4
    SKELETON_CONFIDENCE_THRESHOLD: float = 0.5
    
    # Status box settings
    STATUS_BOX_POSITION: tuple = (10, 30)
    STATUS_BOX_FONT_SCALE: float = 0.6
    STATUS_BOX_FONT_THICKNESS: int = 2
    STATUS_BOX_COLOR: tuple = (255, 255, 255)
    
    # ==================== Session Management ====================
    # Session settings
    SESSION_TIMEOUT: int = int(os.getenv("SESSION_TIMEOUT", 3600))  # 1 hour
    MAX_CONCURRENT_SESSIONS: int = int(
        os.getenv("MAX_CONCURRENT_SESSIONS", 10)
    )
    
    # Cleanup settings
    AUTO_CLEANUP_ENABLED: bool = os.getenv(
        "AUTO_CLEANUP_ENABLED", "True"
    ).lower() == "true"
    CLEANUP_AFTER_HOURS: int = int(os.getenv("CLEANUP_AFTER_HOURS", 24))
    
    # ==================== WebSocket Configuration ====================
    # WebSocket settings
    WS_HEARTBEAT_INTERVAL: int = 20  # seconds
    WS_MAX_MESSAGE_SIZE: int = 10 * 1024 * 1024  # 10MB
    WS_PING_TIMEOUT: int = 30  # seconds
    
    # ==================== Logging Configuration ====================
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Path = BASE_DIR / "app.log"
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # ==================== Performance Configuration ====================
    # Performance settings
    ENABLE_PROFILING: bool = os.getenv(
        "ENABLE_PROFILING", "False"
    ).lower() == "true"
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", 4))
    
    # ==================== Helper Methods ====================
    
    @classmethod
    def initialize_folders(cls):
        """Create necessary directories if they don't exist"""
        cls.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        cls.OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
        cls.SAMPLE_FOLDER.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_mediapipe_config(cls) -> Dict[str, Any]:
        """Get MediaPipe configuration dictionary"""
        return {
            "model_complexity": cls.MEDIAPIPE_MODEL_COMPLEXITY,
            "min_detection_confidence": cls.MEDIAPIPE_MIN_DETECTION_CONFIDENCE,
            "min_tracking_confidence": cls.MEDIAPIPE_MIN_TRACKING_CONFIDENCE,
            "smooth_landmarks": cls.MEDIAPIPE_SMOOTH_LANDMARKS
        }
    
    @classmethod
    def get_video_output_config(cls) -> Dict[str, Any]:
        """Get video output configuration"""
        return {
            "codec": cls.OUTPUT_VIDEO_CODEC,
            "fps": cls.OUTPUT_VIDEO_FPS,
            "quality": cls.OUTPUT_VIDEO_QUALITY
        }
    
    @classmethod
    def get_api_config(cls) -> Dict[str, Any]:
        """Get API configuration"""
        return {
            "host": cls.API_HOST,
            "port": cls.API_PORT,
            "debug": cls.DEBUG,
            "cors_origins": cls.CORS_ORIGINS
        }
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration settings"""
        try:
            # Check model complexity range
            assert 0 <= cls.MEDIAPIPE_MODEL_COMPLEXITY <= 2, \
                "Model complexity must be 0, 1, or 2"
            
            # Check confidence thresholds
            assert 0.0 <= cls.MEDIAPIPE_MIN_DETECTION_CONFIDENCE <= 1.0, \
                "Detection confidence must be between 0.0 and 1.0"
            assert 0.0 <= cls.MEDIAPIPE_MIN_TRACKING_CONFIDENCE <= 1.0, \
                "Tracking confidence must be between 0.0 and 1.0"
            
            # Check file size limit
            assert cls.MAX_FILE_SIZE > 0, "Max file size must be positive"
            
            # Check FPS
            assert cls.TARGET_FPS > 0, "Target FPS must be positive"
            
            # Check port range
            assert 1 <= cls.API_PORT <= 65535, "Port must be between 1 and 65535"
            
            return True
            
        except AssertionError as e:
            print(f"Configuration validation failed: {e}")
            return False
    
    @classmethod
    def print_config(cls):
        """Print current configuration"""
        print("=" * 70)
        print("Current Configuration")
        print("=" * 70)
        print(f"API Host: {cls.API_HOST}")
        print(f"API Port: {cls.API_PORT}")
        print(f"Debug Mode: {cls.DEBUG}")
        print(f"Max File Size: {cls.MAX_FILE_SIZE / (1024*1024):.0f} MB")
        print(f"Max Video Duration: {cls.MAX_VIDEO_DURATION}s")
        print(f"MediaPipe Model: Complexity {cls.MEDIAPIPE_MODEL_COMPLEXITY}")
        print(f"Detection Confidence: {cls.MEDIAPIPE_MIN_DETECTION_CONFIDENCE}")
        print(f"Upload Folder: {cls.UPLOAD_FOLDER}")
        print(f"Output Folder: {cls.OUTPUT_FOLDER}")
        print("=" * 70)


# Validate configuration on import
if not Config.validate_config():
    raise RuntimeError("Invalid configuration. Please check environment variables.")


# Initialize folders on import
Config.initialize_folders()


if __name__ == "__main__":
    # Test configuration
    Config.print_config()
