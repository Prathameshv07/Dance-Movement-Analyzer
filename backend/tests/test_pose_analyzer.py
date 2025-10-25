"""
Unit tests for PoseAnalyzer
Tests pose detection accuracy, keypoint extraction, and skeleton overlay
"""

import pytest
import numpy as np
import cv2
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.pose_analyzer import PoseAnalyzer, PoseKeypoints
from app.config import Config


class TestPoseAnalyzer:
    """Test suite for PoseAnalyzer functionality"""
    
    @pytest.fixture
    def analyzer(self):
        """Create PoseAnalyzer instance for testing"""
        return PoseAnalyzer()
    
    @pytest.fixture
    def sample_frame(self):
        """Create a sample frame for testing"""
        # Create a simple test image (640x480)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Draw a simple stick figure for testing
        # This won't be detected as a real pose, but tests the pipeline
        cv2.circle(frame, (320, 100), 30, (255, 255, 255), -1)  # Head
        cv2.line(frame, (320, 130), (320, 300), (255, 255, 255), 5)  # Body
        cv2.line(frame, (320, 150), (250, 250), (255, 255, 255), 3)  # Left arm
        cv2.line(frame, (320, 150), (390, 250), (255, 255, 255), 3)  # Right arm
        cv2.line(frame, (320, 300), (280, 450), (255, 255, 255), 3)  # Left leg
        cv2.line(frame, (320, 300), (360, 450), (255, 255, 255), 3)  # Right leg
        
        return frame
    
    def test_analyzer_initialization(self, analyzer):
        """Test that PoseAnalyzer initializes correctly"""
        assert analyzer is not None
        assert analyzer.pose is not None
        assert analyzer.mp_pose is not None
        assert len(analyzer.keypoints_history) == 0
    
    def test_process_frame_structure(self, analyzer, sample_frame):
        """Test process_frame returns correct structure or None"""
        result = analyzer.process_frame(sample_frame, frame_number=0, timestamp=0.0)
        
        # Result can be None (no pose detected) or PoseKeypoints
        if result is not None:
            assert isinstance(result, PoseKeypoints)
            assert result.landmarks.shape == (33, 3)
            assert result.frame_number == 0
            assert result.timestamp == 0.0
            assert 0.0 <= result.confidence <= 1.0
    
    def test_process_empty_frame(self, analyzer):
        """Test processing an empty black frame"""
        black_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = analyzer.process_frame(black_frame, frame_number=0, timestamp=0.0)
        
        # Black frame should not detect any pose
        assert result is None or result.confidence < Config.SKELETON_CONFIDENCE_THRESHOLD
    
    def test_draw_skeleton_overlay_no_pose(self, analyzer, sample_frame):
        """Test drawing skeleton when no pose is detected"""
        annotated = analyzer.draw_skeleton_overlay(sample_frame, None)
        
        assert annotated is not None
        assert annotated.shape == sample_frame.shape
        # Should have "No pose detected" text
        assert not np.array_equal(annotated, sample_frame)
    
    def test_draw_skeleton_overlay_with_pose(self, analyzer):
        """Test drawing skeleton with valid pose keypoints"""
        # Create mock PoseKeypoints
        mock_landmarks = np.random.rand(33, 3)
        mock_landmarks[:, 2] = 0.9  # High confidence
        
        mock_pose = PoseKeypoints(
            landmarks=mock_landmarks,
            frame_number=0,
            timestamp=0.0,
            confidence=0.9
        )
        
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        annotated = analyzer.draw_skeleton_overlay(test_frame, mock_pose)
        
        assert annotated is not None
        assert annotated.shape == test_frame.shape
        # Annotated frame should be different from original
        assert not np.array_equal(annotated, test_frame)
    
    def test_process_video_batch(self, analyzer, sample_frame):
        """Test batch processing of frames"""
        frames = [sample_frame.copy() for _ in range(5)]
        
        results = analyzer.process_video_batch(
            frames=frames,
            start_frame_number=0,
            fps=30.0
        )
        
        assert len(results) == 5
        # All results should be None or PoseKeypoints
        for result in results:
            assert result is None or isinstance(result, PoseKeypoints)
    
    def test_get_keypoints_array_empty(self, analyzer):
        """Test getting keypoints array when no frames processed"""
        keypoints = analyzer.get_keypoints_array()
        assert keypoints.size == 0
    
    def test_get_keypoints_array_with_data(self, analyzer):
        """Test getting keypoints array with processed data"""
        # Add mock keypoints to history
        for i in range(3):
            mock_landmarks = np.random.rand(33, 3)
            mock_pose = PoseKeypoints(
                landmarks=mock_landmarks,
                frame_number=i,
                timestamp=i/30.0,
                confidence=0.8
            )
            analyzer.keypoints_history.append(mock_pose)
        
        keypoints = analyzer.get_keypoints_array()
        assert keypoints.shape == (3, 33, 3)
    
    def test_get_average_confidence_empty(self, analyzer):
        """Test average confidence with no data"""
        avg_conf = analyzer.get_average_confidence()
        assert avg_conf == 0.0
    
    def test_get_average_confidence_with_data(self, analyzer):
        """Test average confidence calculation"""
        confidences = [0.7, 0.8, 0.9]
        
        for i, conf in enumerate(confidences):
            mock_landmarks = np.random.rand(33, 3)
            mock_pose = PoseKeypoints(
                landmarks=mock_landmarks,
                frame_number=i,
                timestamp=i/30.0,
                confidence=conf
            )
            analyzer.keypoints_history.append(mock_pose)
        
        avg_conf = analyzer.get_average_confidence()
        expected = np.mean(confidences)
        assert abs(avg_conf - expected) < 0.001
    
    def test_reset_analyzer(self, analyzer):
        """Test resetting analyzer clears history"""
        # Add some data
        mock_landmarks = np.random.rand(33, 3)
        mock_pose = PoseKeypoints(
            landmarks=mock_landmarks,
            frame_number=0,
            timestamp=0.0,
            confidence=0.8
        )
        analyzer.keypoints_history.append(mock_pose)
        
        assert len(analyzer.keypoints_history) == 1
        
        analyzer.reset()
        assert len(analyzer.keypoints_history) == 0
    
    def test_confidence_color_mapping(self, analyzer):
        """Test confidence color mapping"""
        # High confidence should be green
        high_color = analyzer._get_confidence_color(0.9)
        assert high_color == (0, 255, 0)
        
        # Medium confidence should be yellow
        med_color = analyzer._get_confidence_color(0.7)
        assert med_color == (0, 255, 255)
        
        # Low confidence should be orange
        low_color = analyzer._get_confidence_color(0.5)
        assert low_color == (0, 165, 255)
    
    def test_landmark_extraction(self, analyzer):
        """Test landmark extraction produces correct shape"""
        # This test requires actual MediaPipe output
        # We'll test the shape expectations
        expected_shape = (33, 3)
        
        # Create mock MediaPipe landmarks
        class MockLandmark:
            def __init__(self, x, y, vis):
                self.x = x
                self.y = y
                self.visibility = vis
        
        class MockPoseLandmarks:
            def __init__(self):
                self.landmark = [
                    MockLandmark(0.5, 0.5, 0.9) for _ in range(33)
                ]
        
        mock_landmarks = MockPoseLandmarks()
        extracted = analyzer._extract_landmarks(mock_landmarks)
        
        assert extracted.shape == expected_shape
        assert np.all((extracted[:, :2] >= 0) & (extracted[:, :2] <= 1))


def test_config_values():
    """Test that Config values are properly set for pose detection"""
    config = Config.get_mediapipe_config()
    
    assert 'model_complexity' in config
    assert 'min_detection_confidence' in config
    assert 'min_tracking_confidence' in config
    assert 'smooth_landmarks' in config
    
    # Validate ranges
    assert 0 <= config['model_complexity'] <= 2
    assert 0.0 <= config['min_detection_confidence'] <= 1.0
    assert 0.0 <= config['min_tracking_confidence'] <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])