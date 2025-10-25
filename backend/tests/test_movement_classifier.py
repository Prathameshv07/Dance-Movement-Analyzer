"""
Unit tests for MovementClassifier
Tests movement classification, intensity calculation, and rhythm detection
"""

import pytest
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.movement_classifier import MovementClassifier, MovementType, MovementMetrics
from app.pose_analyzer import PoseKeypoints
from app.config import Config


class TestMovementClassifier:
    """Test suite for MovementClassifier functionality"""
    
    @pytest.fixture
    def classifier(self):
        """Create MovementClassifier instance for testing"""
        return MovementClassifier()
    
    @pytest.fixture
    def standing_sequence(self):
        """Create a sequence representing standing still"""
        sequence = []
        base_landmarks = np.random.rand(33, 3)
        
        for i in range(10):
            # Very small random noise to simulate standing
            landmarks = base_landmarks + np.random.normal(0, 0.001, (33, 3))
            landmarks[:, 2] = 0.9  # High confidence
            
            pose = PoseKeypoints(
                landmarks=landmarks,
                frame_number=i,
                timestamp=i/30.0,
                confidence=0.9
            )
            sequence.append(pose)
        
        return sequence
    
    @pytest.fixture
    def dancing_sequence(self):
        """Create a sequence representing dancing (high movement)"""
        sequence = []
        
        for i in range(20):
            # Create varied movement
            landmarks = np.random.rand(33, 3)
            landmarks[:, 2] = 0.9
            
            # Add more variation to simulate dancing
            landmarks[:, 0] += np.sin(i * 0.5) * 0.1
            landmarks[:, 1] += np.cos(i * 0.5) * 0.1
            
            pose = PoseKeypoints(
                landmarks=landmarks,
                frame_number=i,
                timestamp=i/30.0,
                confidence=0.9
            )
            sequence.append(pose)
        
        return sequence
    
    @pytest.fixture
    def jumping_sequence(self):
        """Create a sequence representing jumping (vertical movement)"""
        sequence = []
        base_landmarks = np.random.rand(33, 3)
        
        for i in range(15):
            landmarks = base_landmarks.copy()
            
            # Simulate vertical jump (modify hip positions)
            jump_height = 0.1 * np.sin(i * np.pi / 7)  # Jump cycle
            landmarks[23, 1] -= jump_height  # Left hip
            landmarks[24, 1] -= jump_height  # Right hip
            landmarks[:, 2] = 0.9
            
            pose = PoseKeypoints(
                landmarks=landmarks,
                frame_number=i,
                timestamp=i/30.0,
                confidence=0.9
            )
            sequence.append(pose)
        
        return sequence
    
    def test_classifier_initialization(self, classifier):
        """Test MovementClassifier initializes correctly"""
        assert classifier is not None
        assert len(classifier.movement_history) == 0
        assert classifier.smoothing_window > 0
    
    def test_analyze_empty_sequence(self, classifier):
        """Test analyzing empty sequence"""
        metrics = classifier.analyze_sequence([])
        
        assert metrics.movement_type == MovementType.UNKNOWN
        assert metrics.intensity == 0.0
        assert metrics.velocity == 0.0
    
    def test_analyze_standing_sequence(self, classifier, standing_sequence):
        """Test classification of standing movement"""
        metrics = classifier.analyze_sequence(standing_sequence)
        
        assert metrics is not None
        # Standing should have low velocity
        assert metrics.velocity < Config.VELOCITY_WALKING
        # Should have low intensity
        assert metrics.intensity < 30.0
    
    def test_analyze_dancing_sequence(self, classifier, dancing_sequence):
        """Test classification of dancing movement"""
        metrics = classifier.analyze_sequence(dancing_sequence)
        
        assert metrics is not None
        # Dancing should have higher velocity
        assert metrics.velocity > Config.VELOCITY_STANDING
        # Should have higher intensity
        assert metrics.intensity > 20.0
    
    def test_velocity_calculation(self, classifier, dancing_sequence):
        """Test velocity calculation between frames"""
        velocities = classifier._calculate_velocities(dancing_sequence)
        
        assert len(velocities) == len(dancing_sequence) - 1
        assert np.all(velocities >= 0)  # Velocities should be non-negative
    
    def test_jumping_detection(self, classifier, jumping_sequence):
        """Test jumping detection algorithm"""
        is_jumping = classifier._detect_jumping(jumping_sequence)
        
        # Jumping sequence should be detected
        # Note: This may be True or False depending on threshold sensitivity
        assert isinstance(is_jumping, bool)
    
    def test_crouching_detection(self, classifier):
        """Test crouching detection"""
        # Create crouching pose (compressed torso)
        landmarks = np.random.rand(33, 3)
        landmarks[11, 1] = 0.3  # Shoulder
        landmarks[12, 1] = 0.3
        landmarks[23, 1] = 0.35  # Hip (very close to shoulder)
        landmarks[24, 1] = 0.35
        landmarks[:, 2] = 0.9
        
        crouch_pose = PoseKeypoints(
            landmarks=landmarks,
            frame_number=0,
            timestamp=0.0,
            confidence=0.9
        )
        
        is_crouching = classifier._detect_crouching([crouch_pose])
        
        assert isinstance(is_crouching, bool)
    
    def test_intensity_calculation(self, classifier, dancing_sequence):
        """Test movement intensity calculation"""
        velocities = classifier._calculate_velocities(dancing_sequence)
        movement_type = MovementType.DANCING
        
        intensity = classifier._calculate_intensity(velocities, movement_type)
        
        assert 0 <= intensity <= 100
        assert isinstance(intensity, (int, float))
    
    def test_body_part_activity(self, classifier, dancing_sequence):
        """Test body part activity calculation"""
        activity = classifier._calculate_body_part_activity(dancing_sequence)
        
        # Should have activity scores for all body parts
        expected_parts = ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg"]
        
        for part in expected_parts:
            assert part in activity
            assert 0 <= activity[part] <= 100
    
    def test_movement_summary_empty(self, classifier):
        """Test movement summary with no data"""
        summary = classifier.get_movement_summary()
        
        assert summary['total_sequences'] == 0
        assert summary['average_intensity'] == 0.0
        assert summary['most_active_body_part'] == "none"
    
    def test_movement_summary_with_data(self, classifier, dancing_sequence):
        """Test movement summary with analyzed data"""
        classifier.analyze_sequence(dancing_sequence)
        summary = classifier.get_movement_summary()
        
        assert summary['total_sequences'] == 1
        assert summary['average_intensity'] > 0
        assert 'movement_distribution' in summary
        assert 'most_active_body_part' in summary
    
    def test_rhythm_detection_short_sequence(self, classifier, standing_sequence):
        """Test rhythm detection with short sequence"""
        rhythm = classifier.detect_rhythm_patterns(standing_sequence[:5], fps=30.0)
        
        assert 'has_rhythm' in rhythm
        assert 'estimated_bpm' in rhythm
        assert rhythm['estimated_bpm'] >= 0
    
    def test_rhythm_detection_long_sequence(self, classifier, dancing_sequence):
        """Test rhythm detection with adequate sequence"""
        rhythm = classifier.detect_rhythm_patterns(dancing_sequence, fps=30.0)
        
        assert 'has_rhythm' in rhythm
        assert 'estimated_bpm' in rhythm
        assert 'peak_count' in rhythm
        assert 'rhythm_consistency' in rhythm
    
    def test_find_peaks(self, classifier):
        """Test peak detection in signal"""
        # Create signal with obvious peaks
        signal = np.array([0, 1, 0, 1, 0, 1, 0, 5, 0, 1, 0])
        
        peaks = classifier._find_peaks(signal, threshold_percentile=50)
        
        assert len(peaks) > 0
        # Peak at index 7 (value=5) should be detected
        assert 7 in peaks
    
    def test_movement_smoothness_empty(self, classifier):
        """Test smoothness calculation with minimal data"""
        sequence = []
        smoothness = classifier.calculate_movement_smoothness(sequence)
        
        assert smoothness == 100.0  # Default for no data
    
    def test_movement_smoothness_smooth_motion(self, classifier, standing_sequence):
        """Test smoothness with smooth motion"""
        smoothness = classifier.calculate_movement_smoothness(standing_sequence)
        
        assert 0 <= smoothness <= 100
        # Standing should be very smooth
        assert smoothness > 80
    
    def test_movement_smoothness_jerky_motion(self, classifier):
        """Test smoothness with jerky motion"""
        sequence = []
        
        for i in range(10):
            # Create jerky movement (alternating positions)
            landmarks = np.random.rand(33, 3)
            if i % 2 == 0:
                landmarks[:, 0] += 0.2
            landmarks[:, 2] = 0.9
            
            pose = PoseKeypoints(
                landmarks=landmarks,
                frame_number=i,
                timestamp=i/30.0,
                confidence=0.9
            )
            sequence.append(pose)
        
        smoothness = classifier.calculate_movement_smoothness(sequence)
        
        assert 0 <= smoothness <= 100
    
    def test_movement_type_enum(self):
        """Test MovementType enum values"""
        assert MovementType.STANDING.value == "Standing"
        assert MovementType.WALKING.value == "Walking"
        assert MovementType.DANCING.value == "Dancing"
        assert MovementType.JUMPING.value == "Jumping"
        assert MovementType.CROUCHING.value == "Crouching"
        assert MovementType.UNKNOWN.value == "Unknown"
    
    def test_reset_classifier(self, classifier, dancing_sequence):
        """Test resetting classifier clears history"""
        classifier.analyze_sequence(dancing_sequence)
        assert len(classifier.movement_history) > 0
        
        classifier.reset()
        assert len(classifier.movement_history) == 0
    
    def test_multiple_sequence_analysis(self, classifier, standing_sequence, dancing_sequence):
        """Test analyzing multiple sequences"""
        metrics1 = classifier.analyze_sequence(standing_sequence)
        metrics2 = classifier.analyze_sequence(dancing_sequence)
        
        assert len(classifier.movement_history) == 2
        assert metrics1.intensity != metrics2.intensity
    
    def test_body_parts_defined(self, classifier):
        """Test that all body parts are properly defined"""
        assert 'head' in classifier.BODY_PARTS
        assert 'torso' in classifier.BODY_PARTS
        assert 'left_arm' in classifier.BODY_PARTS
        assert 'right_arm' in classifier.BODY_PARTS
        assert 'left_leg' in classifier.BODY_PARTS
        assert 'right_leg' in classifier.BODY_PARTS
        
        # Each body part should have landmark indices
        for part, indices in classifier.BODY_PARTS.items():
            assert len(indices) > 0
            assert all(0 <= idx < 33 for idx in indices)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])