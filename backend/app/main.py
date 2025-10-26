"""
FastAPI Application with Optimized Startup for Hugging Face Spaces
"""

from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path
import asyncio
import json
import uuid
import shutil
from typing import Optional, Dict, Any
import logging
from datetime import datetime
import numpy as np

from .config import Config
from .video_processor import VideoProcessor
from .utils import validate_file_extension, format_file_size, timing_decorator
from fastapi.templating import Jinja2Templates

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global processor instance (initialized on startup)
global_processor: Optional[VideoProcessor] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler - models already downloaded in Docker build"""
    global global_processor
    
    # Startup
    logger.info("🚀 Starting Dance Movement Analyzer...")
    
    # Initialize folders
    Config.initialize_folders()
    logger.info("✅ Folders initialized")
    
    # Initialize VideoProcessor (models already downloaded, just instantiate)
    logger.info("📦 Initializing Video Processor...")
    try:
        global_processor = VideoProcessor()
        logger.info("✅ Video Processor initialized successfully")
    except Exception as e:
        logger.error(f"❌ Error initializing Video Processor: {e}")
        # Continue anyway - will retry on first request
        global_processor = None
    
    logger.info("🎉 Application startup complete!")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down application...")
    if global_processor is not None:
        # Cleanup if needed
        pass

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Dance Movement Analysis API",
    description="AI-powered dance movement analysis with pose detection and classification",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = Path(__file__).parent.parent.parent / "frontend"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

templates = Jinja2Templates(directory=static_path)

# Active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

# Processing sessions
processing_sessions: Dict[str, Dict[str, Any]] = {}

def convert_to_native_bool(obj):
    """Recursively convert numpy types to native Python types."""
    if isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    elif isinstance(obj, dict):
        return {k: convert_to_native_bool(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_native_bool(v) for v in obj]
    else:
        return obj

class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected: {session_id}")
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected: {session_id}")
    
    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {session_id}: {e}")
                self.disconnect(session_id)
    
    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        disconnected = []
        for session_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(session_id)
        
        for session_id in disconnected:
            self.disconnect(session_id)

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/info")
async def root():
    """Root endpoint - serves API info"""
    return {
        "name": "Dance Movement Analysis API",
        "version": "1.0.0",
        "status": "online",
        "models_loaded": global_processor is not None,
        "endpoints": {
            "upload": "/api/upload",
            "analyze": "/api/analyze/{session_id}",
            "download": "/api/download/{session_id}",
            "websocket": "/ws/{session_id}",
            "docs": "/api/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "models_loaded": global_processor is not None,
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(processing_sessions),
        "active_connections": len(manager.active_connections)
    }

@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    """Upload a video file for processing"""
    from typing import List
    allowed_extensions: List[str] = [".mp4", ".avi", ".mov", ".mkv", ".webm"]

    try:
        session_id = str(uuid.uuid4())

        # Validate file
        validation = validate_file_extension(file.filename, allowed_extensions)
        if not validation["valid"]:
            raise HTTPException(status_code=400, detail=validation["error"])
        
        # Save uploaded file
        upload_path = Config.UPLOAD_FOLDER / f"{session_id}_{file.filename}"
        
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Use pre-initialized processor
        processor = global_processor or VideoProcessor()
        video_info = processor.load_video(upload_path)
        
        # Store session info
        processing_sessions[session_id] = {
            "filename": file.filename,
            "upload_path": str(upload_path),
            "upload_time": datetime.now().isoformat(),
            "status": "uploaded",
            "video_info": video_info
        }
        
        logger.info(f"File uploaded: {session_id} - {file.filename}")
        
        return {
            "success": True,
            "session_id": session_id,
            "filename": file.filename,
            "size": format_file_size(video_info["size_bytes"]),
            "duration": f"{video_info['duration']:.1f}s",
            "resolution": f"{video_info['width']}x{video_info['height']}",
            "fps": video_info["fps"],
            "frame_count": video_info["frame_count"]
        }
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/api/analyze/{session_id}")
async def analyze_video(session_id: str):
    """
    Start video analysis for uploaded file
    
    Args:
        session_id: Session ID from upload
        
    Returns:
        JSON indicating analysis started
    """
    try:
        # Check if session exists
        if session_id not in processing_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = processing_sessions[session_id]
        
        if session["status"] != "uploaded":
            raise HTTPException(
                status_code=400,
                detail=f"Invalid session status: {session['status']}"
            )
        
        # Update status
        session["status"] = "processing"
        session["start_time"] = datetime.now().isoformat()
        
        # Start async processing
        asyncio.create_task(process_video_async(session_id))
        
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


# async def process_video_async(session_id: str):
#     """
#     Async video processing task
    
#     Args:
#         session_id: Session ID to process
#     """
#     try:
#         session = processing_sessions[session_id]
#         input_path = Path(session["upload_path"])
#         output_path = Config.OUTPUT_FOLDER / f"analyzed_{session_id}.mp4"
#         results_path = Config.OUTPUT_FOLDER / f"results_{session_id}.json"
        
#         # Create processor
#         processor = VideoProcessor()
        
#         # Create progress callback
#         async def progress_cb(progress: float, message: str):
#             await manager.send_message(session_id, {
#                 "type": "progress",
#                 "progress": progress,
#                 "message": message,
#                 "timestamp": datetime.now().isoformat()
#             })
        
#         # Process video
#         await manager.send_message(session_id, {
#             "type": "status",
#             "status": "processing",
#             "message": "Starting pose detection..."
#         })
        
#         # Run processing in thread pool to avoid blocking
#         loop = asyncio.get_event_loop()
#         results = await loop.run_in_executor(
#             None,
#             lambda: processor.process_video(
#                 video_path=input_path,
#                 output_path=output_path,
#                 progress_callback=lambda p, m: asyncio.run(progress_cb(p, m))
#             )
#         )
        
#         # ✅ Convert NumPy objects before saving or storing
#         results = convert_to_native_bool(raw_results)

#         # Save clean JSON results
#         with open(results_path, 'w') as f:
#             json.dump(results, f, indent=2, default=str)
        
#         # Update session
#         session["status"] = "completed"
#         session["output_path"] = str(output_path)
#         session["results_path"] = str(results_path)
#         session["end_time"] = datetime.now().isoformat()
#         session["results"] = results
        
#         # Before sending the message, convert results:
#         print("Before sending the message, we convert results here")
#         results = convert_to_native_bool(results)

#         # Send completion message
#         await manager.send_message(session_id, {
#             "type": "complete",
#             "status": "completed",
#             "message": "Analysis complete!",
#             "results": results,
#             "download_url": f"/api/download/{session_id}"
#         })
        
#         logger.info(f"Processing completed: {session_id}")
        
#     except Exception as e:
#         logger.error(f"Processing error for {session_id}: {str(e)}")
        
#         session["status"] = "failed"
#         session["error"] = str(e)
        
#         await manager.send_message(session_id, {
#             "type": "error",
#             "status": "failed",
#             "message": f"Processing failed: {str(e)}"
#         })

async def process_video_async(session_id: str):
    try:
        session = processing_sessions[session_id]
        input_path = Path(session["upload_path"])
        output_path = Config.OUTPUT_FOLDER / f"analyzed_{session_id}.mp4"
        results_path = Config.OUTPUT_FOLDER / f"results_{session_id}.json"
        
        processor = VideoProcessor()

        async def progress_cb(progress: float, message: str):
            await manager.send_message(session_id, {
                "type": "progress",
                "progress": progress,
                "message": message,
                "timestamp": datetime.now().isoformat()
            })

        await manager.send_message(session_id, {
            "type": "status",
            "status": "processing",
            "message": "Starting pose detection..."
        })

        loop = asyncio.get_event_loop()
        raw_results = await loop.run_in_executor(
            None,
            lambda: processor.process_video(
                video_path=input_path,
                output_path=output_path,
                progress_callback=lambda p, m: asyncio.run(progress_cb(p, m))
            )
        )

        # ✅ Convert NumPy objects before saving or storing
        results = convert_to_native_bool(raw_results)

        # Save clean JSON results
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        session.update({
            "status": "completed",
            "output_path": str(output_path),
            "results_path": str(results_path),
            "end_time": datetime.now().isoformat(),
            "results": results
        })

        # Send final WebSocket message
        await manager.send_message(session_id, {
            "type": "complete",
            "status": "completed",
            "message": "Analysis complete!",
            "results": results,
            "download_url": f"/api/download/{session_id}"
        })

        logger.info(f"Processing completed: {session_id}")

    except Exception as e:
        logger.error(f"Processing error for {session_id}: {str(e)}")
        session["status"] = "failed"
        session["error"] = str(e)

        await manager.send_message(session_id, {
            "type": "error",
            "status": "failed",
            "message": f"Processing failed: {str(e)}"
        })

@app.get("/api/results/{session_id}")
async def get_results(session_id: str):
    """
    Get analysis results for a session
    
    Args:
        session_id: Session ID
        
    Returns:
        JSON with analysis results
    """
    if session_id not in processing_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = processing_sessions[session_id]
    
    if session["status"] != "completed":
        return {
            "status": session["status"],
            "message": "Processing not complete"
        }

    # ✅ Ensure safe serialization
    safe_results = convert_to_native_bool(session.get("results", {}))
    
    return {
        "success": True,
        "session_id": session_id,
        "status": session["status"],
        # "results": session.get("results", {}),
        "results": safe_results,
        "download_url": f"/api/download/{session_id}"
    }


@app.get("/api/download/{session_id}")
async def download_video(session_id: str):
    """
    Download processed video
    
    Args:
        session_id: Session ID
        
    Returns:
        Video file
    """
    if session_id not in processing_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = processing_sessions[session_id]
    
    if session["status"] != "completed":
        raise HTTPException(status_code=400, detail="Processing not complete")
    
    output_path = Path(session["output_path"])
    
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Output file not found")
    
    # ✅ Use StreamingResponse to support range requests (needed by HTML5 video)
    def iterfile():
        with open(output_path, mode="rb") as file_like:
            yield from file_like

    return StreamingResponse(
        iterfile(),
        media_type="video/mp4",  # ✅ Ensure correct MIME type
        headers={
            "Accept-Ranges": "bytes",  # ✅ Allow browser seeking
            "Content-Disposition": f'inline; filename="analyzed_{session["filename"]}"'
        }
    )
    
    # return FileResponse(
    #     path=output_path,
    #     media_type="video/mp4",
    #     filename=f"analyzed_{session['filename']}"
    # )


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time updates
    
    Args:
        websocket: WebSocket connection
        session_id: Session ID to monitor
    """
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
            # Wait for messages (heartbeat)
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


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session and its files
    
    Args:
        session_id: Session ID to delete
        
    Returns:
        Success message
    """
    if session_id not in processing_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = processing_sessions[session_id]
    
    # Delete files
    try:
        if "upload_path" in session:
            Path(session["upload_path"]).unlink(missing_ok=True)
        if "output_path" in session:
            Path(session["output_path"]).unlink(missing_ok=True)
        if "results_path" in session:
            Path(session["results_path"]).unlink(missing_ok=True)
    except Exception as e:
        logger.error(f"Error deleting files: {str(e)}")
    
    # Remove session
    del processing_sessions[session_id]
    
    return {
        "success": True,
        "message": "Session deleted",
        "session_id": session_id
    }


@app.get("/api/sessions")
async def list_sessions():
    """
    List all active sessions
    
    Returns:
        List of sessions with their status
    """
    sessions = []
    
    for session_id, session in processing_sessions.items():
        sessions.append({
            "session_id": session_id,
            "filename": session["filename"],
            "status": session["status"],
            "upload_time": session["upload_time"]
        })
    
    return {
        "success": True,
        "count": len(sessions),
        "sessions": sessions
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=Config.API_HOST,
        port=Config.API_PORT,
        log_level="info"
    )