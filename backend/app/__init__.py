"""
Dance Movement Analyzer - AI/ML Server for Dance Video Analysis
Provides pose detection, movement classification, and rhythm analysis
"""

__version__ = "1.0.0"
__author__ = "Your Name"

from .config import Config
from .pose_analyzer import PoseAnalyzer, PoseKeypoints
from .movement_classifier import MovementClassifier, MovementType, MovementMetrics
from .video_processor import VideoProcessor
from .utils import (
    generate_session_id,
    validate_file_extension,
    validate_file_size,
    timing_decorator
)

__all__ = [
    'Config',
    'PoseAnalyzer',
    'PoseKeypoints',
    'MovementClassifier',
    'MovementType',
    'MovementMetrics',
    'VideoProcessor',
    'generate_session_id',
    'validate_file_extension',
    'validate_file_size',
    'timing_decorator'
]