"""
API Routes
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from datetime import datetime
from pathlib import Path
import asyncio
import logging

from app.config import Config
from app.services.session_manager import session_manager
from app.services.video_service import video_service
from app.services.processing_service import processing_service
from app.api.websocket import manager
from app.models.responses import (
    HealthResponse,
    SessionListResponse,
    ResultsResponse
)
from app.utils.file_utils import generate_session_id
from app.services.cleanup_service import cleanup_service

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        models_loaded=video_service.processor is not None,
        models_ready=True,
        timestamp=datetime.now().isoformat(),
        active_sessions=session_manager.get_active_count()
    )


@router.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    """Upload a video file for processing"""
    try:
        session_id = generate_session_id()
        
        # Validate file
        validation = video_service.validate_video(file.filename)
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail=validation["error"])
        
        # Save uploaded file
        upload_path = video_service.save_upload(file, session_id, file.filename)
        
        # Load video info
        video_info = video_service.load_video_info(upload_path)
        
        # Create session
        session_manager.create_session(
            session_id=session_id,
            filename=file.filename,
            upload_path=str(upload_path),
            video_info=video_info
        )
        
        logger.info(f"File uploaded: {session_id} - {file.filename}")
        
        return {
            "success": True,
            "session_id": session_id,
            **video_info
        }
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# @router.post("/api/analyze/{session_id}")
# async def analyze_video(session_id: str):
#     """Start video analysis for uploaded file"""
#     try:
#         # Check if session exists
#         session = session_manager.get_session(session_id)
#         if not session:
#             raise HTTPException(status_code=404, detail="Session not found")
        
#         if session["status"] != "uploaded":
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Invalid session status: {session['status']}"
#             )
        
#         # Update status
#         session_manager.update_session(session_id, {
#             "status": "processing",
#             "start_time": datetime.now().isoformat()
#         })
        
#         # Start async processing
#         asyncio.create_task(
#             processing_service.process_video_async(session_id, manager)
#         )
        
#         return {
#             "success": True,
#             "message": "Analysis started",
#             "session_id": session_id,
#             "websocket_url": f"/ws/{session_id}"
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Analysis error: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/api/analyze/{session_id}")
async def analyze_video(session_id: str):
    """Start video analysis with Celery worker"""
    try:
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session["status"] != "uploaded":
            raise HTTPException(
                status_code=400,
                detail=f"Invalid session status: {session['status']}"
            )
        
        # Start processing with Celery
        task_info = processing_service.start_processing(session_id)
        
        return {
            "success": True,
            "message": "Analysis queued",
            "session_id": session_id,
            "task_id": task_info["task_id"],
            "poll_url": f"/api/task/{task_info['task_id']}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/api/task/{task_id}")
async def get_task_status(task_id: str):
    """Get Celery task status (polling endpoint)"""
    try:
        status = processing_service.get_task_status(task_id)
        return {
            "success": True,
            "task_id": task_id,
            **status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/api/results/{session_id}", response_model=ResultsResponse)
async def get_results(session_id: str):
    """Get analysis results for a session"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session["status"] != "completed":
        return ResultsResponse(
            success=False,
            session_id=session_id,
            status=session["status"],
            results=None,
            download_url=None
        )
    
    # Convert results to ensure JSON serialization
    from app.services.processing_service import convert_to_native_bool
    safe_results = convert_to_native_bool(session.get("results", {}))
    
    return ResultsResponse(
        success=True,
        session_id=session_id,
        status=session["status"],
        results=safe_results,
        download_url=f"/api/download/{session_id}"
    )


@router.get("/api/download/{session_id}")
async def download_video(session_id: str):
    """Download processed video"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session["status"] != "completed":
        raise HTTPException(status_code=400, detail="Processing not complete")
    
    output_path = Path(session["output_path"])
    
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Output file not found")
    
    # Get file size
    file_size = output_path.stat().st_size
    
    # Stream video
    def iterfile():
        with open(output_path, mode="rb") as file_like:
            chunk_size = 8192
            while True:
                chunk = file_like.read(chunk_size)
                if not chunk:
                    break
                yield chunk
    
    return StreamingResponse(
        iterfile(),
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
            "Content-Disposition": f'inline; filename="analyzed_{session["filename"]}"',
            "Cache-Control": "no-cache",
            "X-Content-Type-Options": "nosniff"
        }
    )


@router.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and its files"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Delete files
    video_service.cleanup_session_files(session)
    
    # Remove session
    session_manager.delete_session(session_id)
    
    return {
        "success": True,
        "message": "Session deleted",
        "session_id": session_id
    }


@router.get("/api/sessions", response_model=SessionListResponse)
async def list_sessions():
    """List all active sessions"""
    sessions = session_manager.list_sessions()
    
    return SessionListResponse(
        success=True,
        count=len(sessions),
        sessions=sessions
    )


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(session_id, websocket)
    
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "message": "WebSocket connected",
            "session_id": session_id
        })
        
        # Keep connection alive
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Echo heartbeat
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
                    
            except asyncio.TimeoutError:
                # Send keepalive
                await websocket.send_json({"type": "keepalive"})
                
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        logger.info(f"Client disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(session_id)

# Add this endpoint
@router.get("/api/admin/storage")
async def get_storage_stats():
    """Get storage statistics (admin endpoint)"""
    return cleanup_service.get_storage_stats()


@router.post("/api/admin/cleanup")
async def trigger_cleanup():
    """Manually trigger cleanup (admin endpoint)"""
    result = await cleanup_service.run_cleanup()
    return {
        "success": True,
        "message": "Cleanup completed",
        **result
    }