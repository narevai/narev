"""
NarevAI Billing Analyzer - Main FastAPI Application
"""

import logging
import os
import subprocess
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import v1

# Import API routers
from app.config import get_settings
from app.database import Base, engine
from app.logger import setup_logging

setup_logging()

settings = get_settings()
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    api = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.api_version,
        debug=settings.debug,
    )

    # Add CORS middleware
    api.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Create database tables
    Base.metadata.create_all(bind=engine)

    # Populate database with demo data if DEMO flag is enabled
    if settings.demo:
        # Log big demo mode banner
        logger.info("=" * 80)
        logger.info("🚨" + " " * 30 + "DEMO MODE" + " " * 30 + "🚨")
        logger.info("=" * 80)
        logger.info("📊 This application is running in DEMO mode")
        logger.info("🔒 All data has been anonymized for demonstration purposes")
        logger.info(
            "⚠️  Real names, account IDs, and sensitive information are replaced"
        )
        logger.info(
            "🎯 Perfect for showcasing FOCUS billing data analysis capabilities"
        )
        logger.info("=" * 80)

        try:
            script_path = (
                Path(__file__).parent / "scripts" / "populate_database_from_csv.py"
            )
            subprocess.run(["python", str(script_path)], check=True)
            logger.info("✅ Demo data populated successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Error populating demo data: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error populating demo data: {e}")

    # New router for new frontend
    api.include_router(v1.router, prefix="/api/v1")

    # API endpoints
    @api.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "environment": settings.environment,
            "version": settings.api_version,
        }

    @api.get("/api/")
    async def api_root():
        return {"message": "Hello from NarevAI API! 🚀", "status": "working"}

    @api.get("/api/test")
    async def test_endpoint():
        return {
            "message": "Test endpoint working!",
            "data": ["item1", "item2", "item3"],
            "timestamp": "2025-01-15T10:30:00Z",
        }

    return api


def setup_static_files(api: FastAPI):
    """Setup static files after all routes are defined"""
    if settings.environment != "development":
        # Production: Use the Vite build files
        static_dir = os.getenv("STATIC_DIR", "/app/static")
        static_path = Path(static_dir)

        logger.debug(f"Static directory: {static_path}")
        logger.debug(f"Static directory exists: {static_path.exists()}")

        if static_path.exists():
            # Debug: List contents
            logger.debug("Static directory contents:")
            for item in static_path.iterdir():
                logger.debug(f"  {item}")

            # Mount Vite build subdirectories explicitly
            # This handles /assets/, /resources/, etc.
            for subdir in static_path.iterdir():
                if subdir.is_dir():
                    logger.debug(f"Mounting /{subdir.name} -> {subdir}")
                    api.mount(
                        f"/{subdir.name}",
                        StaticFiles(directory=str(subdir)),
                        name=subdir.name,
                    )

            # SPA fallback for all non-API routes
            from fastapi.responses import FileResponse

            @api.get("/{full_path:path}")
            async def spa_fallback(full_path: str):
                if not full_path.startswith("api/") and not full_path.startswith(
                    "health"
                ):
                    index_path = static_path / "index.html"
                    if index_path.exists():
                        return FileResponse(index_path)
                from fastapi import HTTPException

                raise HTTPException(status_code=404, detail="Not Found")

            # Mount the root static directory for other files (sw.js, favicon.ico, etc.)
            api.mount("/", StaticFiles(directory=str(static_path)), name="static")

        else:
            logger.error(f"Error: Static directory {static_path} does not exist!")

    else:
        # Development mode - no frontend dev server
        logger.info(
            "Running in development mode - use production build for static files"
        )


# Create app instance
app = create_app()
setup_static_files(app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )
