"""
Analytics API - FOCUS Use Cases Implementation
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.schemas.analytics import (
    AnalyticsHealthCheckResponse,
    ApplicationCostTrendResponse,
    AvailableServicesResponse,
    CapacityReservationAnalysisResponse,
    ConnectedProvidersResponse,
    ContractedSavingsResponse,
    EffectiveCostByCurrencyResponse,
    NotImplementedResponse,
    RecurringCommitmentChargesResponse,
    RefundsBySubaccountResponse,
    ResourceRateResponse,
    ResourceUsageResponse,
    ServiceCategoryBreakdownResponse,
    ServiceCostAnalysisResponse,
    ServiceCostByRegionResponse,
    ServiceCostBySubaccountResponse,
    ServiceCostTrendResponse,
    SKUMeteredCostsResponse,
    SpendingByBillingPeriodResponse,
    TagCoverageResponse,
    UnitEconomicsResponse,
    UnusedCapacityResponse,
    UseCaseListResponse,
    UseCaseMetadata,
    VirtualCurrencyPurchaseResponse,
    VirtualCurrencyTargetResponse,
)
from app.services.analytics_service import AnalyticsService

from .deps import get_analytics_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])

# Path to metadata file
METADATA_FILE = Path("metadata/analytics/use_cases.json")

# Cache for metadata
_metadata_cache = None


def load_all_metadata() -> dict[str, Any]:
    """Load all use cases metadata from file."""
    global _metadata_cache

    if _metadata_cache is None:
        try:
            with open(METADATA_FILE) as f:
                _metadata_cache = json.load(f)
        except Exception:
            # Return empty dict on error
            _metadata_cache = {}

    return _metadata_cache


def get_metadata(use_case_id: str) -> dict[str, Any]:
    """Get metadata for specific use case."""
    all_metadata = load_all_metadata()
    return all_metadata.get(
        use_case_id,
        {
            "name": f"Use case {use_case_id}",
            "endpoint": f"/analytics/{use_case_id}",
            "method": "GET",
            "status": "not_implemented",
            "context": "Metadata not available",
            "related_personas": [],
            "related_capabilities": [],
            "focus_columns": [],
            "example_filters": {},
        },
    )


def create_not_implemented_response(use_case_id: str) -> NotImplementedResponse:
    """Helper to create not implemented response."""
    metadata_dict = get_metadata(use_case_id)
    metadata = UseCaseMetadata(**metadata_dict)

    return NotImplementedResponse(
        status="not_implemented",
        metadata=metadata,
        message="This endpoint is not implemented yet",
    )


# List all use cases with filtering
@router.get("/", response_model=UseCaseListResponse)
def list_use_cases(
    persona: str | None = Query(None, description="Filter by related persona"),
    capability: str | None = Query(None, description="Filter by related capability"),
) -> UseCaseListResponse:
    """List all available analytics use cases with optional filtering."""
    all_metadata = load_all_metadata()

    use_cases = []
    for use_case_id, metadata in all_metadata.items():
        # Apply filters if provided
        if persona and persona not in metadata.get("related_personas", []):
            continue
        if capability and capability not in metadata.get("related_capabilities", []):
            continue

        use_cases.append(
            {
                "id": use_case_id,
                "endpoint": metadata.get(
                    "endpoint", f"/analytics/{use_case_id.replace('_', '-')[3:]}"
                ),
                "name": metadata.get("name", ""),
                "context": metadata.get("context", ""),
                "related_personas": metadata.get("related_personas", []),
                "related_capabilities": metadata.get("related_capabilities", []),
                "status": metadata.get("status", "not_implemented"),
            }
        )

    # Get unique personas and capabilities for filter options
    all_personas = set()
    all_capabilities = set()
    for metadata in all_metadata.values():
        all_personas.update(metadata.get("related_personas", []))
        all_capabilities.update(metadata.get("related_capabilities", []))

    return UseCaseListResponse(
        use_cases=use_cases,
        total=len(use_cases),
        filters={
            "available_personas": sorted(all_personas),
            "available_capabilities": sorted(all_capabilities),
            "applied_filters": {"persona": persona, "capability": capability},
        },
    )


# 1. Calculate average rate of a component resource
@router.get("/resource-rate", response_model=ResourceRateResponse)
def calculate_resource_rate(
    start_date: datetime = Query(..., description="Start date for analysis"),
    end_date: datetime = Query(..., description="End date for analysis"),
    provider_name: str | None = Query(None, description="Filter by provider name"),
    service_name: str | None = Query(None, description="Filter by service name"),
    region_name: str | None = Query(None, description="Filter by region name"),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> ResourceRateResponse:
    """Calculate average rate of a component resource."""
    try:
        result = analytics_service.calculate_resource_rate(
            start_date=start_date,
            end_date=end_date,
            provider_name=provider_name,
            service_name=service_name,
            region_name=region_name,
        )

        metadata_dict = get_metadata("01_resource_rate")
        metadata = UseCaseMetadata(**metadata_dict)

        if result["status"] == "error":
            return ResourceRateResponse(
                status="error", message=result["message"], metadata=metadata
            )

        # Add metadata to successful response
        return ResourceRateResponse(**result, metadata=metadata)

    except Exception as e:
        logger.error(f"Error in resource rate endpoint: {e}")
        metadata = get_metadata("01_resource_rate")
        return ResourceRateResponse(
            status="error",
            message="Internal server error",
            metadata=UseCaseMetadata(**metadata),
        )


# 2. Quantify usage of a component resource
@router.get("/resource-usage", response_model=ResourceUsageResponse)
def quantify_resource_usage(
    start_date: datetime = Query(..., description="Start date for analysis"),
    end_date: datetime = Query(..., description="End date for analysis"),
    provider_name: str | None = Query(None, description="Filter by provider name"),
    service_name: str | None = Query(None, description="Filter by service name"),
    region_name: str | None = Query(None, description="Filter by region name"),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> ResourceUsageResponse:
    """Quantify usage of a component resource."""
    try:
        result = analytics_service.quantify_resource_usage(
            start_date=start_date,
            end_date=end_date,
            provider_name=provider_name,
            service_name=service_name,
            region_name=region_name,
        )

        metadata_dict = get_metadata("02_resource_usage")
        metadata = UseCaseMetadata(**metadata_dict)

        if result["status"] == "error":
            return ResourceUsageResponse(
                status="error", message=result["message"], metadata=metadata
            )

        return ResourceUsageResponse(**result, metadata=metadata)

    except Exception as e:
        logger.error(f"Error in resource usage endpoint: {e}")
        metadata = get_metadata("02_resource_usage")
        return ResourceUsageResponse(
            status="error",
            message="Internal server error",
            metadata=UseCaseMetadata(**metadata),
        )


# 3. Calculate unit economics
@router.get("/unit-economics", response_model=UnitEconomicsResponse)
def calculate_unit_economics(
    start_date: datetime = Query(..., description="Start date for analysis"),
    end_date: datetime = Query(..., description="End date for analysis"),
    unit_type: str = Query("GB", description="Unit type to analyze (e.g., GB, Hours)"),
    charge_description_filter: str = Query(
        "transfer", description="Filter for charge description"
    ),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> UnitEconomicsResponse:
    """Calculate unit economics."""
    try:
        result = analytics_service.calculate_unit_economics(
            start_date=start_date,
            end_date=end_date,
            unit_type=unit_type,
            charge_description_filter=charge_description_filter,
        )

        metadata_dict = get_metadata("03_unit_economics")
        metadata = UseCaseMetadata(**metadata_dict)

        if result["status"] == "error":
            return UnitEconomicsResponse(
                status="error", message=result["message"], metadata=metadata
            )

        return UnitEconomicsResponse(**result, metadata=metadata)

    except Exception as e:
        logger.error(f"Error in unit economics endpoint: {e}")
        metadata = get_metadata("03_unit_economics")
        return UnitEconomicsResponse(
            status="error",
            message="Internal server error",
            metadata=UseCaseMetadata(**metadata),
        )


# 4. Determine target of virtual currency usage
@router.get("/virtual-currency-target", response_model=VirtualCurrencyTargetResponse)
def analyze_virtual_currency_target(
    start_date: datetime = Query(..., description="Start date for analysis"),
    end_date: datetime = Query(..., description="End date for analysis"),
    pricing_currency: str | None = Query(
        None, description="Filter by specific pricing currency"
    ),
    limit: int = Query(10, description="Maximum number of results to return"),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> VirtualCurrencyTargetResponse:
    """Determine target of virtual currency usage."""
    try:
        result = analytics_service.analyze_virtual_currency_target(
            start_date=start_date,
            end_date=end_date,
            pricing_currency=pricing_currency,
            limit=limit,
        )

        metadata_dict = get_metadata("04_virtual_currency_target")
        metadata = UseCaseMetadata(**metadata_dict)

        if result["status"] == "error":
            return VirtualCurrencyTargetResponse(
                status="error", message=result["message"], metadata=metadata
            )

        return VirtualCurrencyTargetResponse(**result, metadata=metadata)

    except Exception as e:
        logger.error(f"Error in virtual currency target endpoint: {e}")
        metadata = get_metadata("04_virtual_currency_target")
        return VirtualCurrencyTargetResponse(
            status="error",
            message="Internal server error",
            metadata=UseCaseMetadata(**metadata),
        )


# 5. Analyze effective cost by pricing currency
@router.get(
    "/effective-cost-by-currency", response_model=EffectiveCostByCurrencyResponse
)
def analyze_effective_cost_by_currency(
    start_date: datetime = Query(..., description="Start date for analysis"),
    end_date: datetime = Query(..., description="End date for analysis"),
    include_exchange_rates: bool = Query(
        False, description="Include exchange rate analysis"
    ),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> EffectiveCostByCurrencyResponse:
    """Analyze effective cost by pricing currency."""
    try:
        result = analytics_service.analyze_effective_cost_by_currency(
            start_date=start_date,
            end_date=end_date,
            include_exchange_rates=include_exchange_rates,
        )

        metadata_dict = get_metadata("05_effective_cost_by_currency")
        metadata = UseCaseMetadata(**metadata_dict)

        if result["status"] == "error":
            return EffectiveCostByCurrencyResponse(
                status="error", message=result["message"], metadata=metadata
            )

        return EffectiveCostByCurrencyResponse(**result, metadata=metadata)

    except Exception as e:
        logger.error(f"Error in effective cost by currency endpoint: {e}")
        metadata = get_metadata("05_effective_cost_by_currency")
        return EffectiveCostByCurrencyResponse(
            status="error",
            message="Internal server error",
            metadata=UseCaseMetadata(**metadata),
        )


# 6. Analyze purchase of virtual currency
@router.get(
    "/virtual-currency-purchases", response_model=VirtualCurrencyPurchaseResponse
)
def analyze_virtual_currency_purchases(
    start_date: datetime = Query(..., description="Start date for analysis"),
    end_date: datetime = Query(..., description="End date for analysis"),
    pricing_unit: str | None = Query(
        None, description="Filter by specific pricing unit"
    ),
    group_by: str = Query("service", description="Grouping method"),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> VirtualCurrencyPurchaseResponse:
    """Analyze purchase of virtual currency."""
    try:
        result = analytics_service.analyze_virtual_currency_purchases(
            start_date=start_date,
            end_date=end_date,
            pricing_unit=pricing_unit,
            group_by=group_by,
        )

        metadata_dict = get_metadata("06_virtual_currency_purchases")
        metadata = UseCaseMetadata(**metadata_dict)

        if result["status"] == "error":
            return VirtualCurrencyPurchaseResponse(
                status="error", message=result["message"], metadata=metadata
            )

        return VirtualCurrencyPurchaseResponse(**result, metadata=metadata)

    except Exception as e:
        logger.error(f"Error in virtual currency purchase endpoint: {e}")
        metadata = get_metadata("06_virtual_currency_purchases")
        return VirtualCurrencyPurchaseResponse(
            status="error",
            message="Internal server error",
            metadata=UseCaseMetadata(**metadata),
        )


# 7. Determine contracted savings by virtual currency
@router.get("/contracted-savings", response_model=ContractedSavingsResponse)
def analyze_contracted_savings(
    start_date: datetime = Query(..., description="Start date for analysis"),
    end_date: datetime = Query(..., description="End date for analysis"),
    commitment_type: str | None = Query(
        None, description="Filter by commitment type (e.g., reserved_instances)"
    ),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> ContractedSavingsResponse:
    """Determine contracted savings by virtual currency."""
    try:
        result = analytics_service.analyze_contracted_savings(
            start_date=start_date, end_date=end_date, commitment_type=commitment_type
        )

        metadata_dict = get_metadata("07_contracted_savings")
        metadata = UseCaseMetadata(**metadata_dict)

        if result["status"] == "error":
            return ContractedSavingsResponse(
                status="error", message=result["message"], metadata=metadata
            )

        return ContractedSavingsResponse(**result, metadata=metadata)

    except Exception as e:
        logger.error(f"Error in contracted savings endpoint: {e}")
        metadata = get_metadata("07_contracted_savings")
        return ContractedSavingsResponse(
            status="error",
            message="Internal server error",
            metadata=UseCaseMetadata(**metadata),
        )


# 8. Analyze tag coverage
@router.get("/tag-coverage", response_model=TagCoverageResponse)
def analyze_tag_coverage(
    start_date: datetime = Query(..., description="Start date for analysis"),
    end_date: datetime = Query(..., description="End date for analysis"),
    provider_name: str | None = Query(None, description="Filter by provider name"),
    required_tags: list[str] = Query(
        [], description="List of required tags to analyze"
    ),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> TagCoverageResponse:
    """Analyze tag coverage."""
    try:
        result = analytics_service.analyze_tag_coverage(
            start_date=start_date,
            end_date=end_date,
            provider_name=provider_name,
            required_tags=required_tags if required_tags else None,
        )

        metadata_dict = get_metadata("08_tag_coverage")
        metadata = UseCaseMetadata(**metadata_dict)

        if result["status"] == "error":
            return TagCoverageResponse(
                status="error", message=result["message"], metadata=metadata
            )

        return TagCoverageResponse(**result, metadata=metadata)

    except Exception as e:
        logger.error(f"Error in tag coverage endpoint: {e}")
        metadata = get_metadata("08_tag_coverage")
        return TagCoverageResponse(
            status="error",
            message="Internal server error",
            metadata=UseCaseMetadata(**metadata),
        )


# 9. Analyze the different metered costs for a particular SKU
@router.get("/sku-metered-costs", response_model=SKUMeteredCostsResponse)
def analyze_sku_metered_costs(
    start_date: datetime = Query(..., description="Start date for analysis"),
    end_date: datetime = Query(..., description="End date for analysis"),
    sku_id: str | None = Query(None, description="Filter by specific SKU ID"),
    provider_name: str | None = Query(None, description="Filter by provider name"),
    limit: int = Query(100, description="Maximum number of results to return"),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> SKUMeteredCostsResponse:
    """Analyze the different metered costs for a particular SKU."""
    try:
        result = analytics_service.analyze_sku_metered_costs(
            start_date=start_date,
            end_date=end_date,
            sku_id=sku_id,
            provider_name=provider_name,
            limit=limit,
        )

        metadata_dict = get_metadata("09_sku_metered_costs")
        metadata = UseCaseMetadata(**metadata_dict)

        if result["status"] == "error":
            return SKUMeteredCostsResponse(
                status="error", message=result["message"], metadata=metadata
            )

        return SKUMeteredCostsResponse(**result, metadata=metadata)

    except Exception as e:
        logger.error(f"Error in SKU metered costs endpoint: {e}")
        metadata = get_metadata("09_sku_metered_costs")
        return SKUMeteredCostsResponse(
            status="error",
            message="Internal server error",
            metadata=UseCaseMetadata(**metadata),
        )


# 10. Report costs by service category and subcategory
@router.get(
    "/service-category-breakdown", response_model=ServiceCategoryBreakdownResponse
)
def get_service_category_breakdown(
    start_date: datetime = Query(..., description="Start date for analysis"),
    end_date: datetime = Query(..., description="End date for analysis"),
    provider_name: str | None = Query(None, description="Filter by provider name"),
    service_category: str | None = Query(
        None, description="Filter by service category"
    ),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> ServiceCategoryBreakdownResponse:
    """Report costs by service category and subcategory."""
    try:
        result = analytics_service.get_service_category_breakdown(
            start_date=start_date,
            end_date=end_date,
            provider_name=provider_name,
            service_category=service_category,
        )

        metadata_dict = get_metadata("10_service_category_breakdown")
        metadata = UseCaseMetadata(**metadata_dict)

        if result["status"] == "error":
            return ServiceCategoryBreakdownResponse(
                status="error", message=result["message"], metadata=metadata
            )

        return ServiceCategoryBreakdownResponse(**result, metadata=metadata)

    except Exception as e:
        logger.error(f"Error in service category breakdown endpoint: {e}")
        metadata = get_metadata("10_service_category_breakdown")
        return ServiceCategoryBreakdownResponse(
            status="error",
            message="Internal server error",
            metadata=UseCaseMetadata(**metadata),
        )


# 11. Analyze capacity reservations on compute costs
@router.get(
    "/capacity-reservation-analysis", response_model=CapacityReservationAnalysisResponse
)
def analyze_capacity_reservations(
    start_date: datetime = Query(..., description="Start date for analysis"),
    end_date: datetime = Query(..., description="End date for analysis"),
    provider_name: str | None = Query(None, description="Filter by provider name"),
    billing_account_id: str | None = Query(
        None, description="Filter by billing account ID"
    ),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> CapacityReservationAnalysisResponse:
    """Analyze capacity reservations on compute costs."""
    try:
        result = analytics_service.analyze_capacity_reservations(
            start_date=start_date,
            end_date=end_date,
            provider_name=provider_name,
            billing_account_id=billing_account_id,
        )

        metadata_dict = get_metadata("11_capacity_reservation_analysis")
        metadata = UseCaseMetadata(**metadata_dict)

        if result["status"] == "error":
            return CapacityReservationAnalysisResponse(
                status="error", message=result["message"], metadata=metadata
            )

        return CapacityReservationAnalysisResponse(**result, metadata=metadata)

    except Exception as e:
        logger.error(f"Error in capacity reservation analysis endpoint: {e}")
        metadata = get_metadata("11_capacity_reservation_analysis")
        return CapacityReservationAnalysisResponse(
            status="error",
            message="Internal server error",
            metadata=UseCaseMetadata(**metadata),
        )


# 12. Identify unused capacity reservations
@router.get("/unused-capacity", response_model=UnusedCapacityResponse)
def identify_unused_capacity(
    start_date: datetime = Query(..., description="Start date for analysis"),
    end_date: datetime = Query(..., description="End date for analysis"),
    provider_name: str | None = Query(None, description="Filter by provider name"),
    billing_account_id: str | None = Query(
        None, description="Filter by billing account ID"
    ),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> UnusedCapacityResponse:
    """Identify unused capacity reservations."""
    try:
        result = analytics_service.identify_unused_capacity(
            start_date=start_date,
            end_date=end_date,
            provider_name=provider_name,
            billing_account_id=billing_account_id,
        )

        metadata_dict = get_metadata("12_unused_capacity")
        metadata = UseCaseMetadata(**metadata_dict)

        if result["status"] == "error":
            return UnusedCapacityResponse(
                status="error", message=result["message"], metadata=metadata
            )

        return UnusedCapacityResponse(**result, metadata=metadata)

    except Exception as e:
        logger.error(f"Error in unused capacity endpoint: {e}")
        metadata = get_metadata("12_unused_capacity")
        return UnusedCapacityResponse(
            status="error",
            message="Internal server error",
            metadata=UseCaseMetadata(**metadata),
        )


# 13. Report refunds by subaccount within a billing period
@router.get("/refunds-by-subaccount", response_model=RefundsBySubaccountResponse)
def get_refunds_by_subaccount(
    start_date: datetime = Query(..., description="Start date for analysis"),
    end_date: datetime = Query(..., description="End date for analysis"),
    provider_name: str | None = Query(None, description="Filter by provider name"),
    billing_account_id: str | None = Query(
        None, description="Filter by billing account ID"
    ),
    service_category: str | None = Query(
        None, description="Filter by service category"
    ),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> RefundsBySubaccountResponse:
    """Report refunds by subaccount within a billing period."""
    try:
        result = analytics_service.get_refunds_by_subaccount(
            start_date=start_date,
            end_date=end_date,
            provider_name=provider_name,
            billing_account_id=billing_account_id,
            service_category=service_category,
        )

        metadata_dict = get_metadata("13_refunds_by_subaccount")
        metadata = UseCaseMetadata(**metadata_dict)

        if result["status"] == "error":
            return RefundsBySubaccountResponse(
                status="error", message=result["message"], metadata=metadata
            )

        return RefundsBySubaccountResponse(**result, metadata=metadata)

    except Exception as e:
        logger.error(f"Error in refunds by subaccount endpoint: {e}")
        metadata = get_metadata("13_refunds_by_subaccount")
        return RefundsBySubaccountResponse(
            status="error",
            message="Internal server error",
            metadata=UseCaseMetadata(**metadata),
        )


# 14. Report recurring charges for commitment-based discounts over a period
@router.get(
    "/recurring-commitment-charges", response_model=RecurringCommitmentChargesResponse
)
def get_recurring_commitment_charges(
    start_date: datetime = Query(..., description="Start date for analysis"),
    end_date: datetime = Query(..., description="End date for analysis"),
    commitment_discount_type: str | None = Query(
        None, description="Filter by commitment discount type"
    ),
    charge_frequency: str = Query("Recurring", description="Charge frequency filter"),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> RecurringCommitmentChargesResponse:
    """Report recurring charges for commitment-based discounts over a period."""
    try:
        result = analytics_service.get_recurring_commitment_charges(
            start_date=start_date,
            end_date=end_date,
            commitment_discount_type=commitment_discount_type,
            charge_frequency=charge_frequency,
        )

        metadata_dict = get_metadata("14_recurring_commitment_charges")
        metadata = UseCaseMetadata(**metadata_dict)

        if result["status"] == "error":
            return RecurringCommitmentChargesResponse(
                status="error", message=result["message"], metadata=metadata
            )

        return RecurringCommitmentChargesResponse(**result, metadata=metadata)

    except Exception as e:
        logger.error(f"Error in recurring commitment charges endpoint: {e}")
        metadata = get_metadata("14_recurring_commitment_charges")
        return RecurringCommitmentChargesResponse(
            status="error",
            message="Internal server error",
            metadata=UseCaseMetadata(**metadata),
        )


# 15. Analyze costs by service name
@router.get("/service-cost-analysis", response_model=ServiceCostAnalysisResponse)
def analyze_service_costs(
    start_date: datetime = Query(..., description="Start date for analysis"),
    end_date: datetime = Query(..., description="End date for analysis"),
    service_name: str = Query(..., description="Service name to analyze"),
    provider_name: str | None = Query(None, description="Filter by provider name"),
    sub_account_id: str | None = Query(None, description="Filter by sub account ID"),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> ServiceCostAnalysisResponse:
    """Analyze costs by service name."""
    try:
        result = analytics_service.analyze_service_costs(
            start_date=start_date,
            end_date=end_date,
            service_name=service_name,
            provider_name=provider_name,
            sub_account_id=sub_account_id,
        )

        metadata_dict = get_metadata("15_service_cost_analysis")
        metadata = UseCaseMetadata(**metadata_dict)

        if result["status"] == "error":
            return ServiceCostAnalysisResponse(
                status="error", message=result["message"], metadata=metadata
            )

        return ServiceCostAnalysisResponse(**result, metadata=metadata)

    except Exception as e:
        logger.error(f"Error in service cost analysis endpoint: {e}")
        metadata = get_metadata("15_service_cost_analysis")
        return ServiceCostAnalysisResponse(
            status="error",
            message="Internal server error",
            metadata=UseCaseMetadata(**metadata),
        )


# 16. Report spending across billing periods for a provider by service category
@router.get(
    "/spending-by-billing-period", response_model=SpendingByBillingPeriodResponse
)
def get_spending_by_billing_period(
    start_date: datetime = Query(..., description="Start date for analysis"),
    end_date: datetime = Query(..., description="End date for analysis"),
    provider_name: str = Query(..., description="Provider name to analyze"),
    service_category: str | None = Query(
        None, description="Filter by service category"
    ),
    billing_account_id: str | None = Query(
        None, description="Filter by billing account ID"
    ),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> SpendingByBillingPeriodResponse:
    """Report spending across billing periods for a provider by service category."""
    try:
        result = analytics_service.get_spending_by_billing_period(
            start_date=start_date,
            end_date=end_date,
            provider_name=provider_name,
            service_category=service_category,
            billing_account_id=billing_account_id,
        )

        metadata_dict = get_metadata("16_spending_by_billing_period")
        metadata = UseCaseMetadata(**metadata_dict)

        if result["status"] == "error":
            return SpendingByBillingPeriodResponse(
                status="error", message=result["message"], metadata=metadata
            )

        return SpendingByBillingPeriodResponse(**result, metadata=metadata)

    except Exception as e:
        logger.error(f"Error in spending by billing period endpoint: {e}")
        metadata = get_metadata("16_spending_by_billing_period")
        return SpendingByBillingPeriodResponse(
            status="error",
            message="Internal server error",
            metadata=UseCaseMetadata(**metadata),
        )


# 17. Analyze service costs by region
@router.get("/service-costs-by-region", response_model=ServiceCostByRegionResponse)
def analyze_service_costs_by_region(
    start_date: datetime = Query(..., description="Start date for analysis"),
    end_date: datetime = Query(..., description="End date for analysis"),
    provider_name: str | None = Query(None, description="Filter by provider name"),
    region_id: str | None = Query(None, description="Filter by region ID"),
    service_name: str | None = Query(None, description="Filter by service name"),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> ServiceCostByRegionResponse:
    """Analyze service costs by region."""
    try:
        result = analytics_service.analyze_service_costs_by_region(
            start_date=start_date,
            end_date=end_date,
            provider_name=provider_name,
            region_id=region_id,
            service_name=service_name,
        )

        metadata_dict = get_metadata("17_service_costs_by_region")
        metadata = UseCaseMetadata(**metadata_dict)

        if result["status"] == "error":
            return ServiceCostByRegionResponse(
                status="error", message=result["message"], metadata=metadata
            )

        return ServiceCostByRegionResponse(**result, metadata=metadata)

    except Exception as e:
        logger.error(f"Error in service costs by region endpoint: {e}")
        metadata = get_metadata("17_service_costs_by_region")
        return ServiceCostByRegionResponse(
            status="error",
            message="Internal server error",
            metadata=UseCaseMetadata(**metadata),
        )


# 18. Report service costs by providers subaccount
@router.get(
    "/service-costs-by-subaccount", response_model=ServiceCostBySubaccountResponse
)
def get_service_costs_by_subaccount(
    start_date: datetime = Query(..., description="Start date for analysis"),
    end_date: datetime = Query(..., description="End date for analysis"),
    sub_account_id: str = Query(..., description="Sub account ID to analyze"),
    provider_name: str = Query(..., description="Provider name to analyze"),
    service_name: str | None = Query(None, description="Filter by service name"),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> ServiceCostBySubaccountResponse:
    """Report service costs by providers subaccount."""
    try:
        result = analytics_service.get_service_costs_by_subaccount(
            start_date=start_date,
            end_date=end_date,
            sub_account_id=sub_account_id,
            provider_name=provider_name,
            service_name=service_name,
        )

        metadata_dict = get_metadata("18_service_costs_by_subaccount")
        metadata = UseCaseMetadata(**metadata_dict)

        if result["status"] == "error":
            return ServiceCostBySubaccountResponse(
                status="error", message=result["message"], metadata=metadata
            )

        return ServiceCostBySubaccountResponse(**result, metadata=metadata)

    except Exception as e:
        logger.error(f"Error in service costs by subaccount endpoint: {e}")
        metadata = get_metadata("18_service_costs_by_subaccount")
        return ServiceCostBySubaccountResponse(
            status="error",
            message="Internal server error",
            metadata=UseCaseMetadata(**metadata),
        )


# 19. Analyze service costs month over month
@router.get("/service-cost-trends", response_model=ServiceCostTrendResponse)
def analyze_service_cost_trends(
    start_date: datetime = Query(..., description="Start date for analysis"),
    end_date: datetime = Query(..., description="End date for analysis"),
    provider_name: str | None = Query(None, description="Filter by provider name"),
    service_name: str | None = Query(None, description="Filter by service name"),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> ServiceCostTrendResponse:
    """Analyze service costs month over month."""
    try:
        result = analytics_service.analyze_service_cost_trends(
            start_date=start_date,
            end_date=end_date,
            provider_name=provider_name,
            service_name=service_name,
        )

        metadata_dict = get_metadata("19_service_cost_trends")
        metadata = UseCaseMetadata(**metadata_dict)

        if result["status"] == "error":
            return ServiceCostTrendResponse(
                status="error", message=result["message"], metadata=metadata
            )

        return ServiceCostTrendResponse(**result, metadata=metadata)

    except Exception as e:
        logger.error(f"Error in service cost trends endpoint: {e}")
        metadata = get_metadata("19_service_cost_trends")
        return ServiceCostTrendResponse(
            status="error",
            message="Internal server error",
            metadata=UseCaseMetadata(**metadata),
        )


# 20. Report application cost month over month
@router.get("/application-cost-trends", response_model=ApplicationCostTrendResponse)
def get_application_cost_trends(
    start_date: datetime = Query(..., description="Start date for analysis"),
    end_date: datetime = Query(..., description="End date for analysis"),
    application_tag: str = Query(..., description="Application tag to analyze"),
    service_name: str | None = Query(None, description="Filter by service name"),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> ApplicationCostTrendResponse:
    """Report application cost month over month."""
    try:
        result = analytics_service.get_application_cost_trends(
            start_date=start_date,
            end_date=end_date,
            application_tag=application_tag,
            service_name=service_name,
        )

        metadata_dict = get_metadata("20_application_cost_trends")
        metadata = UseCaseMetadata(**metadata_dict)

        if result["status"] == "error":
            return ApplicationCostTrendResponse(
                status="error", message=result["message"], metadata=metadata
            )

        return ApplicationCostTrendResponse(**result, metadata=metadata)

    except Exception as e:
        logger.error(f"Error in application cost trends endpoint: {e}")
        metadata = get_metadata("20_application_cost_trends")
        return ApplicationCostTrendResponse(
            status="error",
            message="Internal server error",
            metadata=UseCaseMetadata(**metadata),
        )


# Get connected provider names endpoint
@router.get("/providers", response_model=ConnectedProvidersResponse)
def get_connected_providers(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> ConnectedProvidersResponse:
    """Get distinct provider names from billing data for connected providers only."""
    try:
        result = analytics_service.get_connected_provider_names()

        if result["status"] == "error":
            return ConnectedProvidersResponse(
                status="error",
                data=[],
                summary={"total_connected_providers": 0, "provider_list": []},
                message=result["message"],
            )

        return ConnectedProvidersResponse(**result)

    except Exception as e:
        logger.error(f"Error in providers endpoint: {e}")
        return ConnectedProvidersResponse(
            status="error",
            data=[],
            summary={"total_connected_providers": 0, "provider_list": []},
            message="Internal server error",
        )


# Services endpoint
@router.get("/services", response_model=AvailableServicesResponse)
def get_available_services(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> AvailableServicesResponse:
    """Get distinct service names from billing data."""
    try:
        result = analytics_service.get_available_service_names()

        if result["status"] == "error":
            return AvailableServicesResponse(
                status="error",
                data=[],
                summary={"total_available_services": 0},
                message=result["message"],
            )

        return AvailableServicesResponse(**result)

    except Exception as e:
        logger.error(f"Error in services endpoint: {e}")
        return AvailableServicesResponse(
            status="error",
            data=[],
            summary={"total_available_services": 0},
            message="Internal server error",
        )


# Health check
@router.get("/health", response_model=AnalyticsHealthCheckResponse)
def analytics_health_check() -> AnalyticsHealthCheckResponse:
    """Health check for analytics API."""
    return AnalyticsHealthCheckResponse(
        status="healthy",
        service="analytics_api",
        timestamp=datetime.now().isoformat(),
    )
