"""
Video Processor - Handles video I/O, frame processing, and overlay generation
Manages the complete video processing pipeline
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List, Tuple
import logging

from app.config import Config
from app.core.pose_analyzer import PoseAnalyzer, PoseKeypoints
from app.core.movement_classifier import MovementClassifier, MovementMetrics
from app.utils.helpers import timing_decorator
from app.utils.file_utils import format_file_size

logger = logging.getLogger(__name__)

import inspect
import asyncio


class VideoProcessor:
    """
    Manages video loading, processing, and output generation
    Coordinates between pose analysis and movement classification
    """
    
    def __init__(self):
        """Initialize video processor with analyzer components"""
        self.pose_analyzer = PoseAnalyzer()
        self.movement_classifier = MovementClassifier()
        self.current_video_path: Optional[Path] = None
        self.video_info: Dict[str, Any] = {}
        logger.info("VideoProcessor initialized")

    def _safe_callback(self, callback, *args, **kwargs):
        """Safely handle async or sync progress callbacks."""
        if inspect.iscoroutinefunction(callback):
            asyncio.create_task(callback(*args, **kwargs))
        else:
            callback(*args, **kwargs)
    
    def load_video(self, video_path: Path) -> Dict[str, Any]:
        """
        Load video and extract metadata
        
        Args:
            video_path: Path to video file
        
        Returns:
            Dictionary with video information
        
        Raises:
            ValueError: If video cannot be loaded
        """
        if not video_path.exists():
            raise ValueError(f"Video file not found: {video_path}")
        
        # Open video with OpenCV
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {video_path}")
        
        # Extract video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        
        cap.release()
        
        # Validate video duration
        if duration > Config.MAX_VIDEO_DURATION:
            raise ValueError(
                f"Video too long: {duration:.1f}s (max: {Config.MAX_VIDEO_DURATION}s)"
            )

        # Store video info
        self.current_video_path = video_path
        size_bytes = video_path.stat().st_size
        self.video_info = {
            "path": str(video_path),
            "filename": video_path.name,
            "fps": fps,
            "frame_count": frame_count,
            "width": width,
            "height": height,
            "duration": duration,
            "size_bytes": size_bytes,
            "size": format_file_size(size_bytes)
        }
        
        logger.info(f"Loaded video: {video_path.name} ({width}x{height}, "
                   f"{fps:.1f} fps, {duration:.1f}s)")
        
        return self.video_info
    
    @timing_decorator
    def process_video(self, video_path: Path, output_path: Path,
                     progress_callback: Optional[Callable[[float, str], None]] = None) -> Dict[str, Any]:
        """
        Process video with pose detection and movement analysis
        
        Args:
            video_path: Input video path
            output_path: Output video path
            progress_callback: Optional callback for progress updates (progress, message)
        
        Returns:
            Dictionary with processing results and analysis
        """
        # Load video info
        video_info = self.load_video(video_path)
        
        # Reset analyzers for fresh processing
        self.pose_analyzer.reset()
        self.movement_classifier.reset()
        
        # Open video for reading
        cap = cv2.VideoCapture(str(video_path))
        
        # Setup video writer with codec fallback
        codecs_to_try = [
            ('avc1', 'H.264'),           # Try H.264 first
            ('mp4v', 'MPEG-4'),          # Fallback to MPEG-4
            ('XVID', 'Xvid'),
            ('MJPG', 'Motion JPEG')
        ]

        out = None
        last_error = None

        for codec_code, codec_name in codecs_to_try:
            try:
                logger.info(f"Trying codec: {codec_name} ({codec_code})")
                fourcc = cv2.VideoWriter_fourcc(*codec_code)
                out = cv2.VideoWriter(
                    str(output_path),
                    fourcc,
                    video_info['fps'],
                    (video_info['width'], video_info['height'])
                )
                
                if out.isOpened():
                    logger.info(f"✅ Successfully initialized VideoWriter with {codec_name} codec")
                    break
                else:
                    logger.warning(f"Failed to open VideoWriter with {codec_name}")
                    out.release()
                    out = None
            except Exception as e:
                logger.warning(f"Error with {codec_name} codec: {e}")
                last_error = e
                if out:
                    out.release()
                out = None

        if out is None or not out.isOpened():
            error_msg = f"Cannot create output video with any codec. Last error: {last_error}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        frame_number = 0
        processed_frames = 0
        all_keypoints: List[PoseKeypoints] = []
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Calculate timestamp
                timestamp = frame_number / video_info['fps']
                
                # Process frame with pose detection
                pose_keypoints = self.pose_analyzer.process_frame(
                    frame, frame_number, timestamp
                )
                
                if pose_keypoints:
                    all_keypoints.append(pose_keypoints)
                    processed_frames += 1
                
                # Draw skeleton overlay
                annotated_frame = self.pose_analyzer.draw_skeleton_overlay(
                    frame, pose_keypoints, draw_confidence=True
                )
                
                # Add processing status box
                annotated_frame = self._add_status_box(
                    annotated_frame, frame_number, video_info, pose_keypoints
                )
                
                # Write frame to output
                out.write(annotated_frame)
                
                # Update progress
                if progress_callback:
                    progress = (frame_number + 1) / video_info['frame_count']
                    message = f"Processing frame {frame_number + 1}/{video_info['frame_count']}"
                    # progress_callback(progress, message)
                    self._safe_callback(progress_callback, progress, message)                    
                
                frame_number += 1
            
        finally:
            cap.release()
            out.release()
        
        # Analyze movement patterns
        if progress_callback:
            progress_callback(0.95, "Analyzing movements...")
        
        movement_metrics = None
        if all_keypoints:
            movement_metrics = self.movement_classifier.analyze_sequence(all_keypoints)
        
        # Get rhythm analysis
        rhythm_analysis = {}
        if all_keypoints:
            rhythm_analysis = self.movement_classifier.detect_rhythm_patterns(
                all_keypoints, video_info['fps']
            )
        
        # Calculate smoothness
        smoothness = 0.0
        if all_keypoints:
            smoothness = self.movement_classifier.calculate_movement_smoothness(
                all_keypoints
            )
        
        # Compile results
        results = {
            "video_info": video_info,
            "processing": {
                "total_frames": frame_number,
                "frames_with_pose": processed_frames,
                "detection_rate": processed_frames / frame_number if frame_number > 0 else 0,
                "output_path": str(output_path)
            },
            "pose_analysis": {
                "average_confidence": self.pose_analyzer.get_average_confidence(),
                "keypoints_detected": len(all_keypoints)
            },
            "movement_analysis": self._format_movement_metrics(movement_metrics) if movement_metrics else {},
            "rhythm_analysis": rhythm_analysis,
            "smoothness_score": smoothness,
            "summary": self.movement_classifier.get_movement_summary()
        }
        
        if progress_callback:
            progress_callback(1.0, "Processing complete!")
        
        logger.info(f"Video processing complete: {output_path.name}")
        
        return results
    
    def _add_status_box(self, frame: np.ndarray, frame_number: int,
                       video_info: Dict[str, Any], 
                       pose_keypoints: Optional[PoseKeypoints]) -> np.ndarray:
        """
        Add status information box to frame
        
        Args:
            frame: Video frame
            frame_number: Current frame number
            video_info: Video metadata
            pose_keypoints: Detected pose keypoints (if any)
        
        Returns:
            Frame with status box
        """
        # Create semi-transparent overlay
        overlay = frame.copy()
        h, w = frame.shape[:2]
        
        # Status box dimensions
        box_height = 120
        box_width = 300
        box_x = w - box_width - 10
        box_y = 10
        
        # Draw semi-transparent rectangle
        cv2.rectangle(
            overlay,
            (box_x, box_y),
            (box_x + box_width, box_y + box_height),
            (0, 0, 0),
            -1
        )
        
        # Blend with original frame
        alpha = 0.6
        frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
        
        # Add text information
        text_x = box_x + 10
        text_y = box_y + 25
        line_height = 25
        
        # Frame info
        frame_text = f"Frame: {frame_number}/{video_info['frame_count']}"
        cv2.putText(frame, frame_text, (text_x, text_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # FPS info
        fps_text = f"FPS: {video_info['fps']:.1f}"
        cv2.putText(frame, fps_text, (text_x, text_y + line_height),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Pose detection status
        if pose_keypoints:
            status_text = "Pose: DETECTED"
            status_color = (0, 255, 0)
            conf_text = f"Conf: {pose_keypoints.confidence:.2f}"
        else:
            status_text = "Pose: NOT DETECTED"
            status_color = (0, 0, 255)
            conf_text = "Conf: N/A"
        
        cv2.putText(frame, status_text, (text_x, text_y + line_height * 2),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 1)
        
        cv2.putText(frame, conf_text, (text_x, text_y + line_height * 3),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
    
    def _format_movement_metrics(self, metrics: MovementMetrics) -> Dict[str, Any]:
        """
        Format movement metrics for JSON serialization
        
        Args:
            metrics: MovementMetrics object
        
        Returns:
            Dictionary with formatted metrics
        """
        return {
            "movement_type": metrics.movement_type.value,
            "intensity": round(metrics.intensity, 2),
            "velocity": round(metrics.velocity, 4),
            "body_part_activity": {
                part: round(activity, 2)
                for part, activity in metrics.body_part_activity.items()
            },
            "frame_range": metrics.frame_range
        }
    
    def extract_frame(self, video_path: Path, frame_number: int) -> Optional[np.ndarray]:
        """
        Extract a specific frame from video
        
        Args:
            video_path: Path to video file
            frame_number: Frame index to extract
        
        Returns:
            Frame as numpy array, or None if extraction fails
        """
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            return None
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        cap.release()
        
        return frame if ret else None
    
    def create_thumbnail(self, video_path: Path, output_path: Path,
                        timestamp: float = 0.0) -> bool:
        """
        Create thumbnail image from video
        
        Args:
            video_path: Path to video file
            output_path: Output image path
            timestamp: Timestamp in seconds for thumbnail
        
        Returns:
            True if successful
        """
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            return False
        
        # Seek to timestamp
        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return False
        
        # Save thumbnail
        success = cv2.imwrite(str(output_path), frame)
        
        return success