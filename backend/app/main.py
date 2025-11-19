"""
FastAPI Application - Main Entry Point
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from pathlib import Path
import logging
import sys

from .config import Config
from .api.routes import router
from .services.cleanup_service import cleanup_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler"""
    # Startup
    logger.info("🚀 Starting DanceDynamics...")
    Config.initialize_folders()
    logger.info("✅ Folders initialized")
    
    # Start cleanup service
    await cleanup_service.start()
    
    logger.info("🎉 Application startup complete!")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down application...")
    await cleanup_service.stop()

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

# Mount static files (frontend)
if sys.platform == "win32":  # Windows
    static_path = Path(__file__).parent.parent.parent / "frontend"
else:  # Linux or Docker
    static_path = Path(__file__).parent.parent / "frontend"

print(f"Static path: {static_path}")

logger.info(f"Frontend path: {static_path.resolve()}")

if static_path.exists() and static_path.is_dir():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    templates = Jinja2Templates(directory=str(static_path))
else:
    templates = Jinja2Templates(directory=str(static_path))
    logger.warning(f"Frontend directory not found at {static_path.resolve()}")

# Include API routes
app.include_router(router)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/info")
async def root():
    """Root endpoint - API info"""
    from app.api.dependencies import global_processor
    
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


def start_web_app():
    """Start the web application"""
    logger.info('🌐 Starting web application...')
    
    try:
        import uvicorn
        logger.info('✅ Uvicorn imported successfully')
        
        uvicorn.run(
            app,
            host=Config.API_HOST,
            port=Config.API_PORT,
            workers=1,
            log_level='info',
            access_log=True
        )
    except ImportError as e:
        logger.error(f'❌ Failed to import uvicorn: {e}')
        sys.exit(1)
    except Exception as e:
        logger.error(f'❌ Failed to start web application: {e}')
        sys.exit(1)


if __name__ == "__main__":
    start_web_app()