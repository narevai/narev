"""
Billing API
"""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.billing import (
    BillingDataResponse,
    BillingSummaryResponse,
    CostTrendsResponse,
    HealthCheckResponse,
    ServiceBreakdownResponse,
    StatisticsResponse,
)
from app.services.billing_service import BillingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


def get_billing_service(db: Session = Depends(get_db)) -> BillingService:
    """Dependency to inject billing service."""
    return BillingService(db)


@router.get("/summary")
def get_billing_summary(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    provider_id: UUID | None = None,
    currency: str | None = Query(
        None, pattern="^[A-Z]{3}$", description="3-letter currency code"
    ),
    billing_service: BillingService = Depends(get_billing_service),
) -> BillingSummaryResponse:
    """Get billing data summary with aggregations."""
    try:
        summary_data = billing_service.get_billing_summary(
            start_date=start_date,
            end_date=end_date,
            provider_id=provider_id,
            currency=currency,
        )
        return BillingSummaryResponse.model_validate(summary_data)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.get("/data")
def get_billing_data(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    provider_id: UUID | None = None,
    service_name: str | None = Query(None, max_length=255),
    service_category: str | None = Query(
        None,
        pattern="^(AI and Machine Learning|Analytics|Compute|Databases|Networking|Storage|Security|Other)$",
    ),
    charge_category: str | None = Query(
        None, pattern="^(Usage|Purchase|Tax|Credit|Adjustment)$"
    ),
    min_cost: float | None = Query(None, ge=0),
    max_cost: float | None = Query(None, ge=0),
    billing_service: BillingService = Depends(get_billing_service),
) -> BillingDataResponse:
    """Get paginated billing data with filters."""
    try:
        billing_data = billing_service.get_billing_data(
            skip=skip,
            limit=limit,
            start_date=start_date,
            end_date=end_date,
            provider_id=provider_id,
            service_name=service_name,
            service_category=service_category,
            charge_category=charge_category,
            min_cost=min_cost,
            max_cost=max_cost,
        )

        return BillingDataResponse.model_validate(billing_data)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        # TODO: Fix this - catching all exceptions and returning 500 is bad practice
        # Should catch specific exceptions or fix the underlying issue
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error retrieving billing data",
        ) from e


@router.get("/services")
def get_cost_by_service(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    provider_id: UUID | None = None,
    limit: int = Query(10, ge=1, le=100),
    billing_service: BillingService = Depends(get_billing_service),
) -> ServiceBreakdownResponse:
    """Get cost breakdown by service."""
    try:
        services_data = billing_service.get_cost_by_service(
            start_date=start_date,
            end_date=end_date,
            provider_id=provider_id,
            limit=limit,
        )

        # Transform to match schema
        response_data = {
            "services": services_data,
            "total_services": len(services_data),
        }

        return ServiceBreakdownResponse.model_validate(response_data)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.get("/trends")
def get_cost_trends(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    provider_id: UUID | None = None,
    group_by: str = Query("day", pattern="^(day|week|month)$"),
    billing_service: BillingService = Depends(get_billing_service),
) -> CostTrendsResponse:
    """Get cost trends over time."""
    try:
        trends_data = billing_service.get_cost_by_period(
            start_date=start_date,
            end_date=end_date,
            provider_id=provider_id,
            group_by=group_by,
        )

        response_data = {
            "trends": trends_data,
            "group_by": group_by,
        }

        return CostTrendsResponse.model_validate(response_data)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.get("/statistics")
def get_billing_statistics(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    provider_id: UUID | None = None,
    billing_service: BillingService = Depends(get_billing_service),
) -> StatisticsResponse:
    """Get billing statistics and metrics."""
    try:
        stats_data = billing_service.get_billing_statistics(
            provider_id=provider_id, start_date=start_date, end_date=end_date
        )

        return StatisticsResponse.model_validate(stats_data)

    except Exception as e:
        # TODO: Fix this - catching all exceptions and returning 500 is bad practice
        # The service likely returns data that doesn't match StatisticsResponse schema
        # This should catch specific exceptions or fix the data/schema mismatch
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving billing statistics",
        ) from e


@router.get("/health")
def billing_health_check() -> HealthCheckResponse:
    """Health check for billing API."""
    return HealthCheckResponse(
        status="healthy",
        service="billing_api",
        timestamp=datetime.now().isoformat(),
    )
