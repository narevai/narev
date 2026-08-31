from fastapi import APIRouter
from loguru import logger

from varne.config import get_settings

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    settings = get_settings()
    logger.debug("Health check requested")
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": settings.api_version,
    }
