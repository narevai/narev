"""
API v1 Router
"""

from fastapi import APIRouter

from . import analytics, billing, config, export, providers, syncs

# Create v1 router
router = APIRouter()

# Include sub-routers
router.include_router(syncs.router)
router.include_router(providers.router)
router.include_router(export.router)
router.include_router(billing.router)
router.include_router(analytics.router)
router.include_router(config.router)
