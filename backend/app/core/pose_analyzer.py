"""
Pose Analyzer - Core MediaPipe pose detection engine
Handles video frame processing and skeleton overlay generation
"""

import cv2
import numpy as np
import mediapipe as mp
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
import logging

from app.config import Config
from app.utils.helpers import timing_decorator

logger = logging.getLogger(__name__)


@dataclass
class PoseKeypoints:
    """Data class for storing pose keypoints from a single frame"""
    landmarks: np.ndarray  # Shape: (33, 3) - x, y, visibility
    frame_number: int
    timestamp: float
    confidence: float  # Average visibility score


class PoseAnalyzer:
    """
    MediaPipe-based pose detection and analysis engine
    Processes video frames to extract body keypoints and generate skeleton overlays
    """
    
    # MediaPipe pose connections for skeleton drawing
    POSE_CONNECTIONS = mp.solutions.pose.POSE_CONNECTIONS
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize pose analyzer with MediaPipe
        
        Args:
            config: Optional configuration dictionary (uses Config class defaults if None)
        """
        self.config = config or Config.get_mediapipe_config()
        
        # Initialize MediaPipe Pose
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Create pose detector instance
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=self.config['model_complexity'],
            smooth_landmarks=self.config['smooth_landmarks'],
            min_detection_confidence=self.config['min_detection_confidence'],
            min_tracking_confidence=self.config['min_tracking_confidence']
        )
        
        self.keypoints_history: List[PoseKeypoints] = []
        logger.info("PoseAnalyzer initialized with MediaPipe Pose")
    
    def process_frame(self, frame: np.ndarray, frame_number: int, 
                     timestamp: float) -> Optional[PoseKeypoints]:
        """
        Process a single video frame to detect pose
        
        Args:
            frame: BGR image from OpenCV
            frame_number: Frame index in video
            timestamp: Timestamp in seconds
        
        Returns:
            PoseKeypoints object if pose detected, None otherwise
        """
        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process frame with MediaPipe
        results = self.pose.process(rgb_frame)
        
        if results.pose_landmarks:
            # Extract landmarks as numpy array
            landmarks = self._extract_landmarks(results.pose_landmarks)
            
            # Calculate average confidence (visibility score)
            confidence = np.mean(landmarks[:, 2])
            
            # Create PoseKeypoints object
            pose_data = PoseKeypoints(
                landmarks=landmarks,
                frame_number=frame_number,
                timestamp=timestamp,
                confidence=confidence
            )
            
            return pose_data
        
        return None
    
    def _extract_landmarks(self, pose_landmarks) -> np.ndarray:
        """
        Extract landmarks from MediaPipe results as numpy array
        
        Args:
            pose_landmarks: MediaPipe pose landmarks object
        
        Returns:
            Numpy array of shape (33, 3) containing x, y, visibility
        """
        landmarks = []
        for landmark in pose_landmarks.landmark:
            landmarks.append([landmark.x, landmark.y, landmark.visibility])
        return np.array(landmarks)
    
    def draw_skeleton_overlay(self, frame: np.ndarray, 
                              pose_keypoints: Optional[PoseKeypoints],
                              draw_confidence: bool = True) -> np.ndarray:
        """
        Draw skeleton overlay on video frame
        
        Args:
            frame: Original BGR frame
            pose_keypoints: Detected pose keypoints
            draw_confidence: Whether to display confidence score
        
        Returns:
            Frame with skeleton overlay
        """
        annotated_frame = frame.copy()
        
        if pose_keypoints is None:
            # Draw "No pose detected" message
            cv2.putText(
                annotated_frame,
                "No pose detected",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )
            return annotated_frame
        
        # Only draw if confidence is above threshold
        if pose_keypoints.confidence < Config.SKELETON_CONFIDENCE_THRESHOLD:
            return annotated_frame
        
        # Get frame dimensions
        h, w = frame.shape[:2]
        
        # Convert normalized coordinates to pixel coordinates
        landmarks_px = pose_keypoints.landmarks.copy()
        landmarks_px[:, 0] *= w  # x coordinates
        landmarks_px[:, 1] *= h  # y coordinates
        
        # Draw connections (skeleton lines)
        for connection in self.POSE_CONNECTIONS:
            start_idx, end_idx = connection
            
            start_point = landmarks_px[start_idx]
            end_point = landmarks_px[end_idx]
            
            # Check visibility of both points
            if (start_point[2] > Config.SKELETON_CONFIDENCE_THRESHOLD and 
                end_point[2] > Config.SKELETON_CONFIDENCE_THRESHOLD):
                
                start_pos = (int(start_point[0]), int(start_point[1]))
                end_pos = (int(end_point[0]), int(end_point[1]))
                
                # Draw line with color gradient based on confidence
                avg_confidence = (start_point[2] + end_point[2]) / 2
                color = self._get_confidence_color(avg_confidence)
                
                cv2.line(
                    annotated_frame,
                    start_pos,
                    end_pos,
                    color,
                    Config.SKELETON_LINE_THICKNESS,
                    cv2.LINE_AA
                )
        
        # Draw keypoints (circles)
        for i, landmark in enumerate(landmarks_px):
            if landmark[2] > Config.SKELETON_CONFIDENCE_THRESHOLD:
                center = (int(landmark[0]), int(landmark[1]))
                color = self._get_confidence_color(landmark[2])
                
                cv2.circle(
                    annotated_frame,
                    center,
                    Config.SKELETON_CIRCLE_RADIUS,
                    color,
                    -1,
                    cv2.LINE_AA
                )
        
        # Draw confidence score
        if draw_confidence:
            confidence_text = f"Confidence: {pose_keypoints.confidence:.2f}"
            cv2.putText(
                annotated_frame,
                confidence_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
        
        # Draw frame info
        frame_text = f"Frame: {pose_keypoints.frame_number}"
        cv2.putText(
            annotated_frame,
            frame_text,
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            1
        )
        
        return annotated_frame
    
    def _get_confidence_color(self, confidence: float) -> Tuple[int, int, int]:
        """
        Get color based on confidence score (green to yellow to red)
        
        Args:
            confidence: Confidence score (0-1)
        
        Returns:
            BGR color tuple
        """
        if confidence >= 0.8:
            return (0, 255, 0)  # Green - high confidence
        elif confidence >= 0.6:
            return (0, 255, 255)  # Yellow - medium confidence
        else:
            return (0, 165, 255)  # Orange - low confidence
    
    @timing_decorator
    def process_video_batch(self, frames: List[np.ndarray], 
                           start_frame_number: int,
                           fps: float) -> List[Optional[PoseKeypoints]]:
        """
        Process a batch of video frames efficiently
        
        Args:
            frames: List of BGR frames
            start_frame_number: Starting frame number
            fps: Video frames per second
        
        Returns:
            List of PoseKeypoints (None for frames without detected pose)
        """
        results = []
        
        for i, frame in enumerate(frames):
            frame_number = start_frame_number + i
            timestamp = frame_number / fps
            
            pose_data = self.process_frame(frame, frame_number, timestamp)
            results.append(pose_data)
            
            if pose_data:
                self.keypoints_history.append(pose_data)
        
        logger.info(f"Processed {len(frames)} frames, detected pose in "
                   f"{sum(1 for r in results if r is not None)} frames")
        
        return results
    
    def get_keypoints_array(self) -> np.ndarray:
        """
        Get all detected keypoints as a numpy array
        
        Returns:
            Array of shape (N, 33, 3) where N is number of detected frames
        """
        if not self.keypoints_history:
            return np.array([])
        
        return np.array([kp.landmarks for kp in self.keypoints_history])
    
    def get_average_confidence(self) -> float:
        """
        Calculate average confidence across all processed frames
        
        Returns:
            Average confidence score
        """
        if not self.keypoints_history:
            return 0.0
        
        confidences = [kp.confidence for kp in self.keypoints_history]
        return np.mean(confidences)
    
    def reset(self):
        """Reset keypoints history for new video processing"""
        self.keypoints_history.clear()
        logger.info("PoseAnalyzer reset")
    
    def __del__(self):
        """Cleanup MediaPipe resources"""
        if hasattr(self, 'pose'):
            self.pose.close()