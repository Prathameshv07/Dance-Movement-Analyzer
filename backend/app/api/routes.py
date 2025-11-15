"""
API Routes - Direct Processing (No Redis/Celery)
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
from app.api.websocket import manager
from app.models.responses import (
    HealthResponse,
    SessionListResponse,
    ResultsResponse
)
from app.utils.file_utils import generate_session_id
from app.services.cleanup_service import cleanup_service

logger = logging.getLogger(__name__)

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


@router.post("/api/analyze/{session_id}")
async def analyze_video(session_id: str):
    """Start video analysis with direct processing"""
    try:
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        if session["status"] != "uploaded":
            raise HTTPException(
                status_code=400,
                detail=f"Invalid session status: {session['status']}"
            )

        logger.info(f"⚡ Starting direct processing for {session_id}")
        
        # Update status
        session_manager.update_session(session_id, {
            "status": "processing",
            "start_time": datetime.now().isoformat()
        })

        # Start async processing
        asyncio.create_task(process_video_direct(session_id))

        return {
            "success": True,
            "message": "Analysis started",
            "session_id": session_id,
            "websocket_url": f"/ws/{session_id}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


async def process_video_direct(session_id: str):
    """Direct video processing (async background task)"""
    from app.core.video_processor import VideoProcessor
    import json

    try:
        session = session_manager.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            return

        input_path = Path(session["upload_path"])
        output_path = Config.OUTPUT_FOLDER / f"analyzed_{session_id}.mp4"
        results_path = Config.OUTPUT_FOLDER / f"results_{session_id}.json"

        # Create processor
        processor = VideoProcessor()

        # Progress callback
        async def progress_callback(progress: float, message: str):
            session_manager.update_session(session_id, {
                "progress": progress,
                "message": message
            })
            
            # Send WebSocket update if connected
            await manager.send_message(session_id, {
                "type": "progress",
                "progress": progress,
                "message": message
            })
            
            logger.info(f"Progress {session_id}: {progress*100:.1f}% - {message}")

        # Process video (blocking call in background task)
        logger.info(f"Processing video: {input_path}")
        
        # Run blocking code in executor to not block event loop
        import asyncio
        loop = asyncio.get_event_loop()
        
        results = await loop.run_in_executor(
            None,
            processor.process_video,
            input_path,
            output_path,
            lambda p, m: asyncio.create_task(progress_callback(p, m))
        )

        # Save JSON
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        # Update session
        session_manager.update_session(session_id, {
            "status": "completed",
            "output_path": str(output_path),
            "results_path": str(results_path),
            "end_time": datetime.now().isoformat(),
            "results": results
        })

        # Send completion notification
        await manager.send_message(session_id, {
            "type": "complete",
            "session_id": session_id,
            "results": results
        })

        logger.info(f"✅ Processing completed: {session_id}")

    except Exception as e:
        logger.error(f"❌ Processing failed for {session_id}: {str(e)}")
        session_manager.update_session(session_id, {
            "status": "failed",
            "error": str(e)
        })
        
        await manager.send_message(session_id, {
            "type": "error",
            "error": str(e)
        })


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

    return ResultsResponse(
        success=True,
        session_id=session_id,
        status=session["status"],
        results=session.get("results", {}),
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

    file_size = output_path.stat().st_size

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

    video_service.cleanup_session_files(session)
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
        await websocket.send_json({
            "type": "connected",
            "message": "WebSocket connected",
            "session_id": session_id
        })

        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)

                if data == "ping":
                    await websocket.send_json({"type": "pong"})

            except asyncio.TimeoutError:
                await websocket.send_json({"type": "keepalive"})

    except WebSocketDisconnect:
        manager.disconnect(session_id)
        logger.info(f"Client disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(session_id)


@router.get("/api/admin/storage")
async def get_storage_stats():
    """Get storage statistics"""
    return cleanup_service.get_storage_stats()


@router.post("/api/admin/cleanup")
async def trigger_cleanup():
    """Manually trigger cleanup"""
    result = await cleanup_service.run_cleanup()
    return {
        "success": True,
        "message": "Cleanup completed",
        **result
    }