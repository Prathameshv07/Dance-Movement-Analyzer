"""
Integration Tests for Dance Movement Analyzer
Tests complete workflows and API integration
"""

import pytest
import asyncio
import os
from pathlib import Path
from fastapi.testclient import TestClient
import cv2
import numpy as np

# Import the FastAPI app
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.main import app

client = TestClient(app)


class TestIntegration:
    """Integration tests for complete workflows"""
    
    @pytest.fixture
    def sample_video(self, tmp_path):
        """Create a sample video file for testing"""
        video_path = tmp_path / "test_dance.mp4"
        
        # Create a simple test video
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(video_path), fourcc, 30.0, (640, 480))
        
        # Write 90 frames (3 seconds at 30 fps)
        for i in range(90):
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            # Add some movement
            x = int(320 + 100 * np.sin(i * 0.1))
            y = int(240 + 50 * np.cos(i * 0.1))
            cv2.circle(frame, (x, y), 30, (255, 255, 255), -1)
            out.write(frame)
        
        out.release()
        return video_path
    
    def test_complete_workflow(self, sample_video):
        """Test complete upload -> analyze -> download workflow"""
        
        # Step 1: Upload video
        with open(sample_video, 'rb') as f:
            response = client.post(
                "/api/upload",
                files={"file": ("test.mp4", f, "video/mp4")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "session_id" in data
        session_id = data["session_id"]
        
        # Step 2: Start analysis
        response = client.post(f"/api/analyze/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Step 3: Wait for processing (in real scenario, use WebSocket)
        import time
        max_wait = 60  # 60 seconds timeout
        waited = 0
        
        while waited < max_wait:
            response = client.get(f"/api/results/{session_id}")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "completed":
                    break
            time.sleep(2)
            waited += 2
        
        assert waited < max_wait, "Processing timed out"
        
        # Step 4: Verify results
        response = client.get(f"/api/results/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "results" in data
        
        results = data["results"]
        assert "processing" in results
        assert "pose_analysis" in results
        assert "movement_analysis" in results
        
        # Step 5: Download processed video
        response = client.get(f"/api/download/{session_id}")
        assert response.status_code == 200
        assert response.headers["content-type"] == "video/mp4"
        assert len(response.content) > 0
    
    def test_invalid_session_handling(self):
        """Test handling of invalid session IDs"""
        
        fake_session_id = "invalid-session-id-12345"
        
        # Try to analyze
        response = client.post(f"/api/analyze/{fake_session_id}")
        assert response.status_code == 404
        
        # Try to get results
        response = client.get(f"/api/results/{fake_session_id}")
        assert response.status_code == 404
        
        # Try to download
        response = client.get(f"/api/download/{fake_session_id}")
        assert response.status_code == 404
    
    def test_concurrent_sessions(self, sample_video):
        """Test handling multiple concurrent sessions"""
        
        session_ids = []
        
        # Upload multiple videos
        for i in range(3):
            with open(sample_video, 'rb') as f:
                response = client.post(
                    "/api/upload",
                    files={"file": (f"test{i}.mp4", f, "video/mp4")}
                )
            assert response.status_code == 200
            session_ids.append(response.json()["session_id"])
        
        # Start all analyses
        for sid in session_ids:
            response = client.post(f"/api/analyze/{sid}")
            assert response.status_code == 200
        
        # Verify sessions list
        response = client.get("/api/sessions")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 3
    
    def test_session_cleanup(self, sample_video):
        """Test session deletion and cleanup"""
        
        # Upload
        with open(sample_video, 'rb') as f:
            response = client.post(
                "/api/upload",
                files={"file": ("test.mp4", f, "video/mp4")}
            )
        session_id = response.json()["session_id"]
        
        # Delete session
        response = client.delete(f"/api/session/{session_id}")
        assert response.status_code == 200
        
        # Verify session is gone
        response = client.get(f"/api/results/{session_id}")
        assert response.status_code == 404
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "active_sessions" in data


class TestAPIEndpoints:
    """Test individual API endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint serves frontend"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_api_docs(self):
        """Test API documentation endpoint"""
        response = client.get("/api/docs")
        assert response.status_code == 200
    
    def test_upload_validation(self):
        """Test file upload validation"""
        
        # Test no file
        response = client.post("/api/upload")
        assert response.status_code == 422
        
        # Test wrong file type
        fake_file = b"not a video"
        response = client.post(
            "/api/upload",
            files={"file": ("test.txt", fake_file, "text/plain")}
        )
        assert response.status_code == 400
    
    def test_analyze_without_upload(self):
        """Test analyze endpoint without prior upload"""
        response = client.post("/api/analyze/nonexistent-session")
        assert response.status_code == 404
    
    def test_cors_headers(self):
        """Test CORS headers are present"""
        response = client.options("/api/upload")
        assert "access-control-allow-origin" in response.headers


class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_malformed_video(self, tmp_path):
        """Test handling of malformed video file"""
        
        # Create a fake video file
        fake_video = tmp_path / "fake.mp4"
        fake_video.write_bytes(b"not a real video file" * 100)
        
        with open(fake_video, 'rb') as f:
            response = client.post(
                "/api/upload",
                files={"file": ("fake.mp4", f, "video/mp4")}
            )
        
        # Should either reject at upload or fail gracefully during processing
        if response.status_code == 200:
            session_id = response.json()["session_id"]
            response = client.post(f"/api/analyze/{session_id}")
            # Processing should fail but not crash
            assert response.status_code in [200, 400, 500]
    
    def test_oversized_file(self):
        """Test handling of oversized file"""
        
        # Create a large fake file (> 100MB)
        large_content = b"x" * (101 * 1024 * 1024)  # 101 MB
        
        response = client.post(
            "/api/upload",
            files={"file": ("large.mp4", large_content, "video/mp4")}
        )
        
        assert response.status_code == 413  # Payload too large


class TestPerformance:
    """Performance and load tests"""
    
    def test_response_times(self):
        """Test API response times are acceptable"""
        import time
        
        # Health check should be fast
        start = time.time()
        response = client.get("/health")
        duration = time.time() - start
        
        assert duration < 0.1  # Should respond in < 100ms
        assert response.status_code == 200
    
    def test_sessions_list_performance(self):
        """Test sessions list endpoint performance"""
        import time
        
        start = time.time()
        response = client.get("/api/sessions")
        duration = time.time() - start
        
        assert duration < 0.5  # Should respond in < 500ms
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
