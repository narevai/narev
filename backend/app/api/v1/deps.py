"""
Dependency injection for v1 API
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.analytics_service import AnalyticsService
from app.services.billing_service import BillingService
from app.services.provider_service import ProviderService
from app.services.sync_service import SyncService


def get_sync_service(db: Session = Depends(get_db)) -> SyncService:
    """Dependency to inject sync service."""
    return SyncService(db)


def get_provider_service(db: Session = Depends(get_db)) -> ProviderService:
    """Dependency to inject provider service."""
    return ProviderService(db)


def get_billing_service(db: Session = Depends(get_db)) -> BillingService:
    """Dependency to inject billing service."""
    return BillingService(db)


def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    """Dependency to inject analytics service."""
    return AnalyticsService(db)
