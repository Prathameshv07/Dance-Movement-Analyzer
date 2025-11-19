"""
FastAPI Application - Main Entry Point (Fixed for HF Spaces)
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path
import logging
import sys
import os

from .config import Config
from .api.routes import router
from .services.cleanup_service import cleanup_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler"""
    # Startup
    logger.info("🚀 Starting DanceDynamics...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Initialize folders
    try:
        Config.initialize_folders()
        logger.info("✅ Folders initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize folders: {e}")
    
    # Start cleanup service
    try:
        await cleanup_service.start()
        logger.info("✅ Cleanup service started")
    except Exception as e:
        logger.error(f"⚠️ Cleanup service failed to start: {e}")
    
    logger.info("🎉 Application startup complete!")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down application...")
    try:
        await cleanup_service.stop()
    except:
        pass

# Initialize FastAPI app
app = FastAPI(
    title="Dance Movement Analysis API",
    description="AI-powered dance movement analysis with pose detection",
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

# Determine frontend path (works in all environments)
def get_frontend_path():
    """Get the correct frontend path regardless of environment"""
    # Try multiple possible locations
    possible_paths = [
        Path(__file__).parent.parent / "frontend",  # backend/app/../frontend
        Path(__file__).parent.parent.parent / "frontend",  # backend/app/../../frontend
        Path("/app/frontend"),  # Docker absolute path
    ]
    
    for path in possible_paths:
        if path.exists() and path.is_dir():
            logger.info(f"✅ Found frontend at: {path.resolve()}")
            return path
    
    logger.warning("⚠️ Frontend directory not found, using default")
    return Path(__file__).parent.parent / "frontend"

static_path = get_frontend_path()

# Mount static files if directory exists
if static_path.exists() and static_path.is_dir():
    try:
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
        logger.info(f"✅ Static files mounted from: {static_path}")
    except Exception as e:
        logger.error(f"❌ Failed to mount static files: {e}")
else:
    logger.error(f"❌ Static files directory not found at: {static_path}")

# Include API routes
app.include_router(router)


@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main HTML page"""
    try:
        index_path = static_path / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        else:
            logger.error(f"❌ index.html not found at {index_path}")
            return HTMLResponse(
                content="<h1>DanceDynamics</h1><p>Frontend files not found. API is available at <a href='/api/docs'>/api/docs</a></p>",
                status_code=200
            )
    except Exception as e:
        logger.error(f"❌ Error serving index.html: {e}")
        return HTMLResponse(
            content=f"<h1>Error</h1><p>{str(e)}</p>",
            status_code=500
        )


@app.get("/info")
async def root():
    """Root endpoint - API info"""
    from app.api.dependencies import global_processor
    
    return {
        "name": "Dance Movement Analysis API",
        "version": "1.0.0",
        "status": "online",
        "models_loaded": global_processor is not None,
        "environment": {
            "is_docker": Config.IS_DOCKER,
            "is_hf_space": Config.IS_HF_SPACE,
            "python_version": sys.version,
            "working_dir": os.getcwd()
        },
        "endpoints": {
            "upload": "/api/upload",
            "analyze": "/api/analyze/{session_id}",
            "download": "/api/download/{session_id}",
            "websocket": "/ws/{session_id}",
            "docs": "/api/docs"
        }
    }


def start_web_app():
    """Start the web application"""
    import uvicorn
    
    # Get port from environment (for HF Spaces) or use default
    port = int(os.getenv("PORT", os.getenv("API_PORT", "7860")))
    host = os.getenv("API_HOST", "0.0.0.0")
    
    logger.info(f'🌐 Starting web application on {host}:{port}')
    
    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            workers=1,
            log_level='info',
            access_log=True,
            timeout_keep_alive=30
        )
    except Exception as e:
        logger.error(f'❌ Failed to start web application: {e}')
        sys.exit(1)


if __name__ == "__main__":
    start_web_app()