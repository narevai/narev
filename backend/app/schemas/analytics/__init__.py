"""
Analytics schemas package
"""

from .base import (
    NotImplementedResponse,
    UseCaseFilters,
    UseCaseListItem,
    UseCaseListResponse,
    UseCaseMetadata,
)
from .capacity_management import (
    CapacityReservationAnalysisResponse,
    UnusedCapacityResponse,
)
from .cost_analysis import (
    ApplicationCostTrendResponse,
    ContractedSavingsResponse,
    EffectiveCostByCurrencyResponse,
    ServiceCostAnalysisResponse,
    ServiceCostByRegionResponse,
    ServiceCostBySubaccountResponse,
    ServiceCostTrendResponse,
)
from .health import AnalyticsHealthCheckResponse
from .providers import (
    ConnectedProvidersResponse,
    ProvidersSummary,
)
from .reporting import (
    RecurringCommitmentChargesResponse,
    RefundsBySubaccountResponse,
    ServiceCategoryBreakdownResponse,
    SKUMeteredCostsResponse,
    SpendingByBillingPeriodResponse,
    TagCoverageResponse,
)
from .resource_rate import ResourceRateResponse
from .resource_usage import ResourceUsageResponse
from .services import (
    AvailableServicesResponse,
    ServiceInfo,
    ServicesSummary,
)
from .unit_economics import UnitEconomicsResponse
from .virtual_currency import (
    VirtualCurrencyPurchaseResponse,
    VirtualCurrencyTargetResponse,
)

__all__ = [
    # Base
    "NotImplementedResponse",
    "UseCaseMetadata",
    "UseCaseListItem",
    "UseCaseFilters",
    "UseCaseListResponse",
    # Resource management
    "ResourceRateResponse",
    "ResourceUsageResponse",
    "UnitEconomicsResponse",
    # Virtual currency
    "VirtualCurrencyTargetResponse",
    "VirtualCurrencyPurchaseResponse",
    # Cost analysis
    "EffectiveCostByCurrencyResponse",
    "ContractedSavingsResponse",
    "ServiceCostAnalysisResponse",
    "ServiceCostByRegionResponse",
    "ServiceCostBySubaccountResponse",
    "ServiceCostTrendResponse",
    "ApplicationCostTrendResponse",
    # Capacity management
    "CapacityReservationAnalysisResponse",
    "UnusedCapacityResponse",
    # Reporting
    "TagCoverageResponse",
    "SKUMeteredCostsResponse",
    "ServiceCategoryBreakdownResponse",
    "RefundsBySubaccountResponse",
    "RecurringCommitmentChargesResponse",
    "SpendingByBillingPeriodResponse",
    # Providers
    "ConnectedProvidersResponse",
    "ProvidersSummary",
    # Services
    "AvailableServicesResponse",
    "ServiceInfo",
    "ServicesSummary",
    # Health
    "AnalyticsHealthCheckResponse",
]
