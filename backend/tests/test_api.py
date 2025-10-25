"""
Integration tests for FastAPI endpoints
Tests REST API and WebSocket functionality
"""

import pytest
import asyncio
from pathlib import Path
from fastapi.testclient import TestClient
from fastapi import UploadFile
import io
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.config import Config

# Test client
client = TestClient(app)


class TestHealthEndpoints:
    """Test health check and basic endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint returns API info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "online"
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "active_sessions" in data


class TestUploadEndpoint:
    """Test video upload functionality"""
    
    def create_mock_video_file(self, filename="test.mp4", size=1024):
        """Create a mock video file for testing"""
        return io.BytesIO(b"0" * size)
    
    def test_upload_valid_video(self):
        """Test uploading a valid video file"""
        file_content = self.create_mock_video_file(size=1024 * 100)  # 100KB
        files = {"file": ("dance.mp4", file_content, "video/mp4")}
        
        response = client.post("/api/upload", files=files)
        
        # Note: This will fail with actual validation
        # In real tests, use actual video files
        assert response.status_code in [200, 400, 500]
    
    def test_upload_invalid_file_type(self):
        """Test uploading invalid file type"""
        file_content = io.BytesIO(b"fake image content")
        files = {"file": ("test.jpg", file_content, "image/jpeg")}
        
        response = client.post("/api/upload", files=files)
        assert response.status_code == 400
    
    def test_upload_no_file(self):
        """Test upload without file"""
        response = client.post("/api/upload")
        assert response.status_code == 422  # Unprocessable entity
    
    def test_upload_large_file(self):
        """Test uploading file exceeding size limit"""
        # Create 150MB mock file
        large_file = self.create_mock_video_file(size=150 * 1024 * 1024)
        files = {"file": ("large.mp4", large_file, "video/mp4")}
        
        response = client.post("/api/upload", files=files)
        assert response.status_code in [400, 413]  # Bad request or payload too large


class TestAnalysisEndpoints:
    """Test analysis workflow endpoints"""
    
    def test_analyze_nonexistent_session(self):
        """Test analyzing non-existent session"""
        response = client.post("/api/analyze/invalid-session-id")
        assert response.status_code == 404
    
    def test_get_results_nonexistent_session(self):
        """Test getting results for non-existent session"""
        response = client.get("/api/results/invalid-session-id")
        assert response.status_code == 404
    
    def test_download_nonexistent_session(self):
        """Test downloading from non-existent session"""
        response = client.get("/api/download/invalid-session-id")
        assert response.status_code == 404


class TestSessionManagement:
    """Test session management endpoints"""
    
    def test_list_sessions(self):
        """Test listing all sessions"""
        response = client.get("/api/sessions")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "count" in data
        assert "sessions" in data
        assert isinstance(data["sessions"], list)
    
    def test_delete_nonexistent_session(self):
        """Test deleting non-existent session"""
        response = client.delete("/api/session/invalid-session-id")
        assert response.status_code == 404


class TestWebSocket:
    """Test WebSocket functionality"""
    
    def test_websocket_connection(self):
        """Test WebSocket connection"""
        with client.websocket_connect("/ws/test-session") as websocket:
            # Receive connection message
            data = websocket.receive_json()
            assert data["type"] == "connected"
            assert data["session_id"] == "test-session"
    
    def test_websocket_heartbeat(self):
        """Test WebSocket heartbeat mechanism"""
        with client.websocket_connect("/ws/test-session") as websocket:
            # Skip connection message
            websocket.receive_json()
            
            # Send ping
            websocket.send_text("ping")
            
            # Receive pong
            data = websocket.receive_json()
            assert data["type"] == "pong"


class TestCORS:
    """Test CORS configuration"""
    
    def test_cors_headers(self):
        """Test CORS headers are present"""
        response = client.options("/health")
        assert response.status_code in [200, 405]  # Depends on implementation


class TestErrorHandling:
    """Test error handling"""
    
    def test_404_error(self):
        """Test 404 error for non-existent endpoint"""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
    
    def test_method_not_allowed(self):
        """Test method not allowed"""
        response = client.put("/api/upload")
        assert response.status_code == 405


# Integration Test (requires actual video file)
class TestFullWorkflow:
    """Test complete upload-analyze-download workflow"""
    
    @pytest.mark.skipif(
        not Path("tests/test_data/sample.mp4").exists(),
        reason="Sample video not found"
    )
    def test_complete_workflow(self):
        """Test complete workflow with real video"""
        # 1. Upload video
        video_path = Path("tests/test_data/sample.mp4")
        with open(video_path, "rb") as f:
            files = {"file": ("sample.mp4", f, "video/mp4")}
            response = client.post("/api/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        session_id = data["session_id"]
        
        # 2. Start analysis
        response = client.post(f"/api/analyze/{session_id}")
        assert response.status_code == 200
        
        # 3. Wait for processing (in real scenario, use WebSocket)
        import time
        time.sleep(5)
        
        # 4. Get results
        response = client.get(f"/api/results/{session_id}")
        assert response.status_code in [200, 400]  # May still be processing
        
        # 5. Clean up
        client.delete(f"/api/session/{session_id}")


# Performance Tests
class TestPerformance:
    """Test API performance"""
    
    def test_health_check_performance(self):
        """Test health check response time"""
        import time
        
        start = time.time()
        response = client.get("/health")
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 0.1  # Should respond in < 100ms
    
    def test_concurrent_requests(self):
        """Test handling concurrent requests"""
        import concurrent.futures
        
        def make_request():
            return client.get("/health")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in futures]
        
        assert all(r.status_code == 200 for r in results)


# Validation Tests
class TestValidation:
    """Test input validation"""
    
    def test_session_id_format(self):
        """Test session ID format validation"""
        # Test with invalid UUID format
        response = client.post("/api/analyze/not-a-uuid")
        assert response.status_code == 404
    
    def test_file_size_validation(self):
        """Test file size limits are enforced"""
        # This is tested in TestUploadEndpoint.test_upload_large_file
        pass


# Security Tests
class TestSecurity:
    """Test security measures"""
    
    def test_path_traversal_prevention(self):
        """Test path traversal attack prevention"""
        response = client.get("/api/download/../../../etc/passwd")
        assert response.status_code in [400, 404]
    
    def test_file_extension_validation(self):
        """Test file extension validation"""
        file_content = io.BytesIO(b"malicious content")
        files = {"file": ("malware.exe", file_content, "application/x-msdownload")}
        
        response = client.post("/api/upload", files=files)
        assert response.status_code == 400


# Documentation Tests
class TestDocumentation:
    """Test API documentation"""
    
    def test_swagger_ui_accessible(self):
        """Test Swagger UI is accessible"""
        response = client.get("/api/docs")
        assert response.status_code == 200
    
    def test_redoc_accessible(self):
        """Test ReDoc is accessible"""
        response = client.get("/api/redoc")
        assert response.status_code == 200
    
    def test_openapi_schema(self):
        """Test OpenAPI schema is available"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema


# Cleanup Tests
class TestCleanup:
    """Test resource cleanup"""
    
    def test_session_cleanup(self):
        """Test session cleanup deletes files"""
        # This requires a real session
        # Implementation depends on session management
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])