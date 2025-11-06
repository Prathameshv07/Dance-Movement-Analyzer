"""
Movement Classifier - Advanced movement intelligence and analysis
Classifies dance movements, calculates intensity, and detects patterns
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging

from app.config import Config
from app.core.pose_analyzer import PoseKeypoints
from app.utils.validation import safe_divide

logger = logging.getLogger(__name__)


class MovementType(Enum):
    """Enumeration of movement types"""
    STANDING = "Standing"
    WALKING = "Walking"
    DANCING = "Dancing"
    JUMPING = "Jumping"
    CROUCHING = "Crouching"
    UNKNOWN = "Unknown"


@dataclass
class MovementMetrics:
    """Data class for movement analysis results"""
    movement_type: MovementType
    intensity: float  # 0-100 scale
    velocity: float  # Average velocity
    body_part_activity: Dict[str, float]  # Activity level per body part
    frame_range: Tuple[int, int]  # Start and end frame numbers


class MovementClassifier:
    """
    Analyzes pose sequences to classify movements and calculate metrics
    """
    
    # Body part groupings using MediaPipe landmark indices
    BODY_PARTS = {
        "head": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],  # Face and head
        "torso": [11, 12, 23, 24],  # Shoulders and hips
        "left_arm": [11, 13, 15, 17, 19, 21],  # Left shoulder to hand
        "right_arm": [12, 14, 16, 18, 20, 22],  # Right shoulder to hand
        "left_leg": [23, 25, 27, 29, 31],  # Left hip to foot
        "right_leg": [24, 26, 28, 30, 32]  # Right hip to foot
    }
    
    def __init__(self, smoothing_window: int = 5):
        """
        Initialize movement classifier
        
        Args:
            smoothing_window: Number of frames for smoothing calculations
        """
        self.smoothing_window = smoothing_window
        self.movement_history: List[MovementMetrics] = []
        logger.info("MovementClassifier initialized")
    
    def analyze_sequence(self, keypoints_sequence: List[PoseKeypoints]) -> MovementMetrics:
        """
        Analyze a sequence of pose keypoints to classify movement
        
        Args:
            keypoints_sequence: List of detected pose keypoints
        
        Returns:
            MovementMetrics object with analysis results
        """
        if not keypoints_sequence:
            return self._create_empty_metrics()
        
        # Calculate velocities between consecutive frames
        velocities = self._calculate_velocities(keypoints_sequence)
        
        # Calculate average velocity (overall movement speed)
        avg_velocity = np.mean(velocities) if len(velocities) > 0 else 0.0
        
        # Classify movement type based on velocity and pose characteristics
        movement_type = self._classify_movement(keypoints_sequence, avg_velocity)
        
        # Calculate movement intensity (0-100 scale)
        intensity = self._calculate_intensity(velocities, movement_type)
        
        # Analyze activity per body part
        body_part_activity = self._calculate_body_part_activity(keypoints_sequence)
        
        # Get frame range
        frame_range = (
            keypoints_sequence[0].frame_number,
            keypoints_sequence[-1].frame_number
        )
        
        metrics = MovementMetrics(
            movement_type=movement_type,
            intensity=intensity,
            velocity=avg_velocity,
            body_part_activity=body_part_activity,
            frame_range=frame_range
        )
        
        self.movement_history.append(metrics)
        
        logger.info(f"Analyzed sequence: {movement_type.value}, "
                   f"Intensity: {intensity:.1f}, Velocity: {avg_velocity:.4f}")
        
        return metrics
    
    def _calculate_velocities(self, keypoints_sequence: List[PoseKeypoints]) -> np.ndarray:
        """
        Calculate frame-to-frame velocities for all keypoints
        
        Args:
            keypoints_sequence: List of pose keypoints
        
        Returns:
            Array of velocities (one per frame transition)
        """
        if len(keypoints_sequence) < 2:
            return np.array([0.0])
        
        velocities = []
        
        for i in range(1, len(keypoints_sequence)):
            prev_landmarks = keypoints_sequence[i-1].landmarks[:, :2]  # x, y only
            curr_landmarks = keypoints_sequence[i].landmarks[:, :2]
            
            # Calculate Euclidean distance for each keypoint
            displacement = np.linalg.norm(curr_landmarks - prev_landmarks, axis=1)
            
            # Average displacement across all keypoints
            avg_displacement = np.mean(displacement)
            
            # Time difference (assuming constant fps)
            time_diff = keypoints_sequence[i].timestamp - keypoints_sequence[i-1].timestamp
            
            # Velocity = displacement / time
            velocity = safe_divide(avg_displacement, time_diff, 0.0)
            velocities.append(velocity)
        
        return np.array(velocities)
    
    def _classify_movement(self, keypoints_sequence: List[PoseKeypoints], 
                          avg_velocity: float) -> MovementType:
        """
        Classify movement type based on velocity and pose characteristics
        
        Args:
            keypoints_sequence: List of pose keypoints
            avg_velocity: Average velocity across sequence
        
        Returns:
            MovementType classification
        """
        # Check for jumping (vertical movement of center of mass)
        if self._detect_jumping(keypoints_sequence):
            return MovementType.JUMPING
        
        # Check for crouching (low body position)
        if self._detect_crouching(keypoints_sequence):
            return MovementType.CROUCHING
        
        # Classify based on velocity thresholds
        if avg_velocity < Config.VELOCITY_STANDING:
            return MovementType.STANDING
        elif avg_velocity < Config.VELOCITY_WALKING:
            return MovementType.WALKING
        elif avg_velocity < Config.VELOCITY_DANCING:
            return MovementType.DANCING
        else:
            # High velocity movements are likely dancing
            return MovementType.DANCING
    
    def _detect_jumping(self, keypoints_sequence: List[PoseKeypoints]) -> bool:
        """
        Detect jumping motion by analyzing vertical hip movement
        
        Args:
            keypoints_sequence: List of pose keypoints
        
        Returns:
            True if jumping detected
        """
        if len(keypoints_sequence) < 5:
            return False
        
        # Get hip positions (landmarks 23 and 24)
        hip_y_positions = []
        for kp in keypoints_sequence:
            left_hip_y = kp.landmarks[23, 1]
            right_hip_y = kp.landmarks[24, 1]
            avg_hip_y = (left_hip_y + right_hip_y) / 2
            hip_y_positions.append(avg_hip_y)
        
        hip_y_positions = np.array(hip_y_positions)
        
        # Calculate vertical velocity
        vertical_velocity = np.abs(np.diff(hip_y_positions))
        
        # Jumping has high vertical velocity peaks
        max_vertical_velocity = np.max(vertical_velocity)
        
        return max_vertical_velocity > Config.VELOCITY_JUMPING
    
    def _detect_crouching(self, keypoints_sequence: List[PoseKeypoints]) -> bool:
        """
        Detect crouching by analyzing hip-to-shoulder distance
        
        Args:
            keypoints_sequence: List of pose keypoints
        
        Returns:
            True if crouching detected
        """
        if not keypoints_sequence:
            return False
        
        # Use middle frame for analysis
        mid_idx = len(keypoints_sequence) // 2
        landmarks = keypoints_sequence[mid_idx].landmarks
        
        # Calculate average shoulder position (landmarks 11, 12)
        shoulder_y = (landmarks[11, 1] + landmarks[12, 1]) / 2
        
        # Calculate average hip position (landmarks 23, 24)
        hip_y = (landmarks[23, 1] + landmarks[24, 1]) / 2
        
        # Calculate torso length
        torso_length = abs(hip_y - shoulder_y)
        
        # Crouching: torso is compressed (small torso length)
        # This is relative, so we use a threshold
        return torso_length < 0.15  # Normalized coordinates
    
    def _calculate_intensity(self, velocities: np.ndarray, 
                            movement_type: MovementType) -> float:
        """
        Calculate movement intensity on 0-100 scale
        
        Args:
            velocities: Array of velocities
            movement_type: Classified movement type
        
        Returns:
            Intensity score (0-100)
        """
        if len(velocities) == 0:
            return 0.0
        
        # Calculate base intensity from velocity
        avg_velocity = np.mean(velocities)
        velocity_std = np.std(velocities)
        
        # Normalize velocity to 0-100 scale
        # Higher velocity and variation = higher intensity
        base_intensity = min(avg_velocity * 500, 70)  # Cap at 70
        variation_bonus = min(velocity_std * 300, 30)  # Up to 30 bonus
        
        raw_intensity = base_intensity + variation_bonus
        
        # Apply movement type multipliers
        multipliers = {
            MovementType.STANDING: 0.1,
            MovementType.WALKING: 0.4,
            MovementType.DANCING: 1.0,
            MovementType.JUMPING: 1.2,
            MovementType.CROUCHING: 0.3,
            MovementType.UNKNOWN: 0.5
        }
        
        intensity = raw_intensity * multipliers.get(movement_type, 1.0)
        
        # Clamp to 0-100 range
        return np.clip(intensity, 0, 100)
    
    def _calculate_body_part_activity(self, 
                                     keypoints_sequence: List[PoseKeypoints]) -> Dict[str, float]:
        """
        Calculate activity level for each body part
        
        Args:
            keypoints_sequence: List of pose keypoints
        
        Returns:
            Dictionary mapping body part names to activity scores (0-100)
        """
        if len(keypoints_sequence) < 2:
            return {part: 0.0 for part in self.BODY_PARTS.keys()}
        
        activity_scores = {}
        
        for part_name, landmark_indices in self.BODY_PARTS.items():
            total_movement = 0.0
            
            # Calculate movement for this body part across all frames
            for i in range(1, len(keypoints_sequence)):
                prev_landmarks = keypoints_sequence[i-1].landmarks[landmark_indices, :2]
                curr_landmarks = keypoints_sequence[i].landmarks[landmark_indices, :2]
                
                # Calculate average movement for this body part
                displacement = np.linalg.norm(curr_landmarks - prev_landmarks, axis=1)
                avg_displacement = np.mean(displacement)
                
                total_movement += avg_displacement
            
            # Normalize to 0-100 scale
            avg_movement = total_movement / (len(keypoints_sequence) - 1)
            activity_score = min(avg_movement * 1000, 100)  # Scale and cap at 100
            
            activity_scores[part_name] = activity_score
        
        return activity_scores
    
    def get_movement_summary(self) -> Dict[str, any]:
        """
        Get summary statistics of all analyzed movements
        
        Returns:
            Dictionary with summary statistics
        """
        if not self.movement_history:
            return {
                "total_sequences": 0,
                "average_intensity": 0.0,
                "movement_distribution": {},
                "most_active_body_part": "none"
            }
        
        # Count movement types
        movement_counts = {}
        for metrics in self.movement_history:
            movement_type = metrics.movement_type.value
            movement_counts[movement_type] = movement_counts.get(movement_type, 0) + 1
        
        # Calculate average intensity
        avg_intensity = np.mean([m.intensity for m in self.movement_history])
        
        # Find most active body part across all sequences
        all_body_parts = {}
        for metrics in self.movement_history:
            for part, activity in metrics.body_part_activity.items():
                if part not in all_body_parts:
                    all_body_parts[part] = []
                all_body_parts[part].append(activity)
        
        avg_body_part_activity = {
            part: np.mean(activities) 
            for part, activities in all_body_parts.items()
        }
        
        most_active_part = max(avg_body_part_activity.items(), key=lambda x: x[1])[0]
        
        return {
            "total_sequences": len(self.movement_history),
            "average_intensity": round(avg_intensity, 2),
            "movement_distribution": movement_counts,
            "most_active_body_part": most_active_part,
            "avg_body_part_activity": {
                k: round(v, 2) for k, v in avg_body_part_activity.items()
            }
        }
    
    def detect_rhythm_patterns(self, keypoints_sequence: List[PoseKeypoints], 
                              fps: float) -> Dict[str, any]:
        """
        Detect rhythmic patterns in movement (basic beat detection)
        
        Args:
            keypoints_sequence: List of pose keypoints
            fps: Video frames per second
        
        Returns:
            Dictionary with rhythm analysis
        """
        if len(keypoints_sequence) < 10:
            return {"has_rhythm": False, "estimated_bpm": 0}
        
        # Calculate velocities
        velocities = self._calculate_velocities(keypoints_sequence)
        
        # Apply smoothing
        if len(velocities) > self.smoothing_window:
            kernel = np.ones(self.smoothing_window) / self.smoothing_window
            smoothed_velocities = np.convolve(velocities, kernel, mode='valid')
        else:
            smoothed_velocities = velocities
        
        # Find peaks in velocity (potential beats)
        peaks = self._find_peaks(smoothed_velocities)
        
        if len(peaks) < 2:
            return {"has_rhythm": False, "estimated_bpm": 0}
        
        # Calculate average time between peaks
        peak_intervals = np.diff(peaks) / fps  # Convert to seconds
        avg_interval = np.mean(peak_intervals)
        
        # Calculate BPM (beats per minute)
        bpm = safe_divide(60, avg_interval, 0)
        
        # Check if rhythm is consistent (low standard deviation)
        interval_std = np.std(peak_intervals)
        is_rhythmic = interval_std < (avg_interval * 0.3)  # Within 30% variation
        
        return {
            "has_rhythm": is_rhythmic,
            "estimated_bpm": round(bpm, 1),
            "peak_count": len(peaks),
            "rhythm_consistency": round(1 - (interval_std / avg_interval), 2) if avg_interval > 0 else 0
        }
    
    def _find_peaks(self, signal: np.ndarray, threshold_percentile: float = 70) -> np.ndarray:
        """
        Find peaks in a signal (simple peak detection)
        
        Args:
            signal: 1D signal array
            threshold_percentile: Percentile threshold for peak detection
        
        Returns:
            Array of peak indices
        """
        if len(signal) < 3:
            return np.array([])
        
        # Calculate threshold
        threshold = np.percentile(signal, threshold_percentile)
        
        peaks = []
        for i in range(1, len(signal) - 1):
            # Peak: higher than neighbors and above threshold
            if (signal[i] > signal[i-1] and 
                signal[i] > signal[i+1] and 
                signal[i] > threshold):
                peaks.append(i)
        
        return np.array(peaks)
    
    def calculate_movement_smoothness(self, keypoints_sequence: List[PoseKeypoints]) -> float:
        """
        Calculate smoothness of movement (lower jerk = smoother)
        
        Args:
            keypoints_sequence: List of pose keypoints
        
        Returns:
            Smoothness score (0-100, higher is smoother)
        """
        if len(keypoints_sequence) < 3:
            return 100.0  # Not enough data
        
        # Calculate velocities
        velocities = self._calculate_velocities(keypoints_sequence)
        
        if len(velocities) < 2:
            return 100.0
        
        # Calculate jerk (rate of change of velocity)
        jerk = np.abs(np.diff(velocities))
        avg_jerk = np.mean(jerk)
        
        # Convert to smoothness score (inverse of jerk)
        # Lower jerk = higher smoothness
        smoothness = max(0, 100 - (avg_jerk * 1000))
        
        return round(smoothness, 2)
    
    def _create_empty_metrics(self) -> MovementMetrics:
        """Create empty metrics for cases with no data"""
        return MovementMetrics(
            movement_type=MovementType.UNKNOWN,
            intensity=0.0,
            velocity=0.0,
            body_part_activity={part: 0.0 for part in self.BODY_PARTS.keys()},
            frame_range=(0, 0)
        )
    
    def reset(self):
        """Reset movement history"""
        self.movement_history.clear()
        logger.info("MovementClassifier reset")