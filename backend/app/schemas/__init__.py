"""
API Schemas Package
"""

from app.schemas.analytics import __all__ as analytics_all
from app.schemas.billing import (
    BillingDataResponse,
    BillingSummaryResponse,
    CostTrendsResponse,
    ServiceBreakdownResponse,
    StatisticsResponse,
)
from app.schemas.export import (
    HealthCheckResponse as ExportHealthCheckResponse,
)
from app.schemas.provider import (
    ProviderCreate,
    ProviderListResponse,
    ProviderResponse,
    ProviderTestResult,
    ProviderUpdate,
)
from app.schemas.sync import (
    SyncActionResponse,
    SyncRunDetails,
    SyncRunsResponse,
    SyncStatisticsResponse,
    SyncStatusResponse,
    SyncTriggerRequest,
    SyncTriggerResponse,
)

__all__ = [
    # Provider schemas
    "ProviderCreate",
    "ProviderUpdate",
    "ProviderResponse",
    "ProviderTestResult",
    "ProviderListResponse",
    # Billing schemas
    "BillingSummaryResponse",
    "BillingDataResponse",
    "ServiceBreakdownResponse",
    "CostTrendsResponse",
    "StatisticsResponse",
    # Sync schemas
    "SyncTriggerRequest",
    "SyncTriggerResponse",
    "SyncStatusResponse",
    "SyncRunsResponse",
    "SyncRunDetails",
    "SyncActionResponse",
    "SyncStatisticsResponse",
    # Export schemas
    "ExportHealthCheckResponse",
] + analytics_all  # All analytics schemas from the analytics module
