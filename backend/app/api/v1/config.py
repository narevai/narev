"""
NarevAI Billing Analyzer - Config API v1
"""

from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(prefix="/config", tags=["config"])


@router.get("")
def get_config():
    """
    Get application configuration.

    Returns basic configuration information including demo mode status.
    """
    settings = get_settings()

    return {"settings": {"demo": settings.demo}}
