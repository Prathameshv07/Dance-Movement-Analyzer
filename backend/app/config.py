"""
Configuration Management - With Optional Redis/Celery Support
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from dataclasses import dataclass, field
from typing import Dict, Any

# Load environment variables
load_dotenv()


@dataclass
class Config:
    """Configuration management for the application"""

    # ==================== Platform Detection ====================
    IS_WINDOWS: bool = sys.platform == "win32"
    IS_DOCKER: bool = os.path.exists("/.dockerenv")
    IS_HF_SPACE: bool = os.getenv("SPACE_ID") is not None

    # ==================== Redis/Celery Configuration ====================
    # Auto-disable Redis on Windows unless explicitly enabled
    USE_REDIS: bool = field(default_factory=lambda: (
        os.getenv("USE_REDIS", "auto").lower() == "true" if os.getenv("USE_REDIS", "auto").lower() != "auto"
        else not (sys.platform == "win32")  # Disable on Windows by default
    ))
    
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    # ==================== API Configuration ====================
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "7860"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # CORS Settings
    CORS_ORIGINS: list = field(default_factory=lambda: os.getenv(
        "CORS_ORIGINS", "*"
    ).split(","))

    # ==================== File Configuration ====================
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
    MEDIAPIPE_MODEL_COMPLEXITY: int = int(
        os.getenv("MEDIAPIPE_MODEL_COMPLEXITY", 0)
    )

    MEDIAPIPE_MIN_DETECTION_CONFIDENCE: float = float(
        os.getenv("MEDIAPIPE_MIN_DETECTION_CONFIDENCE", 0.5)
    )
    MEDIAPIPE_MIN_TRACKING_CONFIDENCE: float = float(
        os.getenv("MEDIAPIPE_MIN_TRACKING_CONFIDENCE", 0.5)
    )

    MEDIAPIPE_SMOOTH_LANDMARKS: bool = os.getenv(
        "MEDIAPIPE_SMOOTH_LANDMARKS", "True"
    ).lower() == "true"

    # ==================== Processing Configuration ====================
    TARGET_FPS: int = int(os.getenv("TARGET_FPS", 30))
    FRAME_SKIP: int = int(os.getenv("FRAME_SKIP", 1))
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", 30))

    OUTPUT_VIDEO_CODEC: str = os.getenv("OUTPUT_VIDEO_CODEC", "mp4v")
    OUTPUT_VIDEO_FPS: int = int(os.getenv("OUTPUT_VIDEO_FPS", 30))
    OUTPUT_VIDEO_QUALITY: int = int(os.getenv("OUTPUT_VIDEO_QUALITY", 90))

    # ==================== Movement Classification ====================
    VELOCITY_STANDING: float = 0.01
    VELOCITY_WALKING: float = 0.03
    VELOCITY_DANCING: float = 0.06
    VELOCITY_JUMPING: float = 0.12

    MOVEMENT_INTENSITY_LOW: float = 0.02
    MOVEMENT_INTENSITY_MEDIUM: float = 0.05
    MOVEMENT_INTENSITY_HIGH: float = 0.08

    MOVEMENT_SMOOTHING_WINDOW: int = 5

    # ==================== Visualization Configuration ====================
    SKELETON_COLOR_HIGH_CONF: tuple = (0, 255, 0)
    SKELETON_COLOR_MED_CONF: tuple = (0, 255, 255)
    SKELETON_COLOR_LOW_CONF: tuple = (0, 165, 255)
    SKELETON_LINE_THICKNESS: int = 2
    SKELETON_CIRCLE_RADIUS: int = 4
    SKELETON_CONFIDENCE_THRESHOLD: float = 0.5

    STATUS_BOX_POSITION: tuple = (10, 30)
    STATUS_BOX_FONT_SCALE: float = 0.6
    STATUS_BOX_FONT_THICKNESS: int = 2
    STATUS_BOX_COLOR: tuple = (255, 255, 255)

    # ==================== Session Management ====================
    SESSION_TIMEOUT: int = int(os.getenv("SESSION_TIMEOUT", 3600))
    MAX_CONCURRENT_SESSIONS: int = int(
        os.getenv("MAX_CONCURRENT_SESSIONS", 10)
    )

    AUTO_CLEANUP_ENABLED: bool = os.getenv(
        "AUTO_CLEANUP_ENABLED", "True"
    ).lower() == "true"
    CLEANUP_AFTER_HOURS: int = int(os.getenv("CLEANUP_AFTER_HOURS", 24))

    # ==================== WebSocket Configuration ====================
    WS_HEARTBEAT_INTERVAL: int = 20
    WS_MAX_MESSAGE_SIZE: int = 10 * 1024 * 1024
    WS_PING_TIMEOUT: int = 30

    # ==================== Logging Configuration ====================
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Path = BASE_DIR / "app.log"
    LOG_MAX_BYTES: int = 10 * 1024 * 1024
    LOG_BACKUP_COUNT: int = 5

    # ==================== Performance Configuration ====================
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
            assert 0 <= cls.MEDIAPIPE_MODEL_COMPLEXITY <= 2, \
                "Model complexity must be 0, 1, or 2"

            assert 0.0 <= cls.MEDIAPIPE_MIN_DETECTION_CONFIDENCE <= 1.0, \
                "Detection confidence must be between 0.0 and 1.0"
            assert 0.0 <= cls.MEDIAPIPE_MIN_TRACKING_CONFIDENCE <= 1.0, \
                "Tracking confidence must be between 0.0 and 1.0"

            assert cls.MAX_FILE_SIZE > 0, "Max file size must be positive"
            assert cls.TARGET_FPS > 0, "Target FPS must be positive"
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
        print(f"Platform: {'Windows' if cls.IS_WINDOWS else 'Linux/Mac'}")
        print(f"Docker: {cls.IS_DOCKER}")
        print(f"HF Space: {cls.IS_HF_SPACE}")
        print(f"Redis Enabled: {cls.USE_REDIS}")
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
    Config.print_config()