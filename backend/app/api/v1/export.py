"""
Export API
"""

import logging
import traceback
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.schemas.export import HealthCheckResponse
from app.services.billing_service import BillingService
from app.services.export_service import ExportService

from .deps import get_billing_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/billing")
def export_billing_data(
    format: str = Query("csv", pattern="^(csv|xlsx)$"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        10000, ge=1, le=50000, description="Number of records to export (max 50k)"
    ),
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
) -> StreamingResponse:
    """Export billing data as file (CSV or XLSX only)."""

    logger.info(
        f"Export request: format={format}, start_date={start_date}, end_date={end_date}"
    )

    try:
        # Get data from billing service
        logger.info("Fetching billing data from service...")
        data = billing_service.get_billing_data(
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

        if not data or not isinstance(data, dict):
            logger.error(f"Invalid data structure returned: {type(data)}")
            raise HTTPException(
                status_code=500,
                detail="Invalid data structure returned from billing service",
            )

        records = data.get("data", [])
        total_records = data.get("pagination", {}).get("total", 0)

        logger.info(
            f"Successfully fetched {len(records)} records out of {total_records} total"
        )

        # Prepare export metadata
        metadata = {
            "total_records": total_records,
            "exported_records": len(records),
            "export_date": datetime.now(UTC),
            "start_date": start_date,
            "end_date": end_date,
            "provider_id": provider_id,
            "service_category": service_category,
            "service_name": service_name,
            "charge_category": charge_category,
            "min_cost": min_cost,
            "max_cost": max_cost,
            "skip": skip,
            "limit": limit,
        }

        # Use generic export service (only CSV/XLSX now)
        result = ExportService.export_data(
            data=records,
            format=format,
            filename_prefix="billing_data",
            metadata=metadata,
        )

        # Result is always StreamingResponse now
        return result

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # TODO: Fix this - catching all exceptions and returning 500 is bad practice
        # Likely cause: data format doesn't match export service expectations
        # Should handle specific exceptions or fix data format issues

        # Log the full traceback for debugging
        logger.error(f"Unexpected error in export_billing_data: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exporting billing data: {str(e)}",
        ) from e


@router.get("/health")
def export_health_check() -> HealthCheckResponse:
    """Health check for export API."""
    return HealthCheckResponse(
        status="healthy",
        service="export_api",
        timestamp=datetime.now().isoformat(),
    )
