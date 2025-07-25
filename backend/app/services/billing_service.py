"""
Billing Service Layer
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.billing_data import BillingData
from app.repositories.billing_repository import BillingRepository
from app.repositories.pipeline_repository import PipelineRepository
from app.repositories.provider_repository import ProviderRepository
from app.services.provider_service import ProviderService
from focus.models import FocusRecord
from focus.validators import FocusValidator

logger = logging.getLogger(__name__)


class BillingService:
    """Service layer for billing operations."""

    def __init__(self, db: Session):
        """Initialize billing service."""
        self.db = db
        self.billing_repo = BillingRepository(db)
        self.pipeline_repo = PipelineRepository(db)
        self.provider_repo = ProviderRepository(db)
        self.provider_service = ProviderService(db)
        self.validator = FocusValidator()

    async def start_sync(
        self,
        provider_id: UUID | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        days_back: int | None = None,
    ) -> dict[str, Any]:
        """
        Start billing data synchronization.

        Args:
            provider_id: Specific provider to sync (optional)
            start_date: Start date for sync
            end_date: End date for sync
            days_back: Days back from now if dates not specified

        Returns:
            Sync status and run IDs
        """
        # Determine date range
        logger.info(
            "Starting billing sync with parameters: "
            f"provider_id={provider_id}, start_date={start_date}, end_date={end_date}, days_back={days_back}"
        )

        start_date, end_date = self._get_date_range(start_date, end_date, days_back)

        logger.info(f"Using date range: {start_date} to {end_date}")

        # Get providers to sync
        if provider_id:
            provider = self.provider_repo.get(provider_id)
            if not provider:
                raise ValueError(f"Provider {provider_id} not found")
            if not provider.is_active:
                raise ValueError(f"Provider {provider_id} is not active")
            providers = [provider]
        else:
            providers = self.provider_repo.get_active_providers_for_sync()

        if not providers:
            raise ValueError("No active providers found")

        # Start pipeline runs for each provider
        run_ids = []
        errors = []

        for provider in providers:
            try:
                result = await self.orchestrator.run_pipeline(
                    provider_id=UUID(provider.id),
                    start_date=start_date,
                    end_date=end_date,
                    run_type="manual",
                )

                run_ids.append(result["pipeline_run_id"])

            except Exception as e:
                logger.error(f"Failed to start sync for provider {provider.id}: {e}")
                errors.append(
                    {
                        "provider_id": provider.id,
                        "provider_name": provider.name,
                        "error": str(e),
                    }
                )

        return {
            "success": len(run_ids) > 0,
            "message": f"Started sync for {len(run_ids)} providers",
            "pipeline_run_ids": run_ids,
            "providers_synced": len(providers),
            "errors": errors,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
        }

    def get_billing_data(
        self,
        skip: int = 0,
        limit: int = 100,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        provider_id: UUID | None = None,
        service_category: str | None = None,
        **filters,
    ) -> dict[str, Any]:
        """
        Get billing data with pagination and filters.

        Args:
            skip: Number of records to skip
            limit: Number of records to return
            start_date: Filter by start date
            end_date: Filter by end date
            provider_id: Filter by provider
            service_category: Filter by service category
            **filters: Additional filters

        Returns:
            Billing data with pagination info
        """
        # Get data from repository
        data, total = self.billing_repo.get_billing_data(
            skip=skip,
            limit=limit,
            start_date=start_date,
            end_date=end_date,
            provider_id=str(provider_id) if provider_id else None,
            service_category=service_category,
            **filters,
        )

        return {
            "data": [self._serialize_billing_record(record) for record in data],
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total,
                "has_more": (skip + limit) < total,
            },
        }

    def get_services_breakdown(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        provider_id: UUID | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Get cost breakdown by service.

        Args:
            start_date: Start of period
            end_date: End of period
            provider_id: Filter by provider
            limit: Maximum number of services to return

        Returns:
            Service breakdown data
        """
        # Default to last 30 days
        start_date, end_date = self._get_date_range(start_date, end_date, 30)

        return self.billing_repo.get_services_breakdown(
            start_date=start_date,
            end_date=end_date,
            provider_id=str(provider_id) if provider_id else None,
            limit=limit,
        )

    def get_cost_by_service(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        provider_id: UUID | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Get cost breakdown by service.

        This is an alias for get_services_breakdown() to match API expectations.

        Args:
            start_date: Start of period
            end_date: End of period
            provider_id: Filter by provider
            limit: Maximum number of services to return

        Returns:
            Service breakdown data
        """
        return self.get_services_breakdown(
            start_date=start_date,
            end_date=end_date,
            provider_id=provider_id,
            limit=limit,
        )

    def get_daily_costs(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        provider_id: UUID | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get daily cost breakdown.

        Args:
            start_date: Start of period
            end_date: End of period
            provider_id: Filter by provider

        Returns:
            Daily cost data
        """
        days_back = 30  # Default to last 30 days if not specified

        start_date, end_date = self._get_date_range(start_date, end_date, days_back)

        return self.billing_repo.get_daily_costs(
            start_date, end_date, provider_id=str(provider_id) if provider_id else None
        )

    def get_billing_summary(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        provider_id: UUID | None = None,
        currency: str | None = None,
    ) -> dict[str, Any]:
        """
        Get billing summary with aggregations.

        Args:
            start_date: Start of period
            end_date: End of period
            provider_id: Filter by provider
            currency: Filter by currency

        Returns:
            Summary with aggregated data
        """
        try:
            days_back = 30  # Default to last 30 days if not specified

            start_date, end_date = self._get_date_range(start_date, end_date, days_back)

            # Get summary from repository
            summary = self.billing_repo.get_summary(
                start_date=start_date,
                end_date=end_date,
                provider_id=str(provider_id) if provider_id else None,
                currency=currency,
            )

            return summary

        except Exception as e:
            logger.error(f"Error getting billing summary: {e}")
            raise

    def get_top_resources(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        provider_id: UUID | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Get top resources by cost.

        Args:
            start_date: Start of period
            end_date: End of period
            provider_id: Filter by provider
            limit: Number of results

        Returns:
            Top resources data
        """
        days_back = 30  # Default to last 30 days if not specified

        start_date, end_date = self._get_date_range(start_date, end_date, days_back)

        return self.billing_repo.get_top_resources(
            start_date,
            end_date,
            provider_id=str(provider_id) if provider_id else None,
            limit=limit,
        )

    def get_top_skus(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        provider_id: UUID | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Get top SKUs by cost.

        Args:
            start_date: Start of period
            end_date: End of period
            provider_id: Filter by provider
            limit: Number of results

        Returns:
            Top SKUs data
        """
        days_back = 30  # Default to last 30 days if not specified

        start_date, end_date = self._get_date_range(start_date, end_date, days_back)

        return self.billing_repo.get_top_skus(
            start_date,
            end_date,
            provider_id=str(provider_id) if provider_id else None,
            limit=limit,
        )

    def get_cost_by_period(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        provider_id: UUID | None = None,
        group_by: str = "day",
    ) -> list[dict[str, Any]]:
        """
        Get cost aggregated by time period.

        Args:
            start_date: Start of period
            end_date: End of period
            provider_id: Filter by provider
            group_by: Grouping ("day", "week", "month")

        Returns:
            Cost data grouped by period
        """
        days_back = 30  # Default to last 30 days if not specified

        start_date, end_date = self._get_date_range(start_date, end_date, days_back)

        return self.billing_repo.get_cost_by_period(
            start_date,
            end_date,
            provider_id=str(provider_id) if provider_id else None,
            group_by=group_by,
        )

    def get_billing_statistics(
        self,
        provider_id: UUID | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Get billing statistics and metrics.

        Args:
            provider_id: Filter by provider
            start_date: Start of period
            end_date: End of period

        Returns:
            Billing statistics that match StatisticsResponse schema
        """
        # Default to last 30 days
        start_date, end_date = self._get_date_range(start_date, end_date, 30)

        # Get basic summary data
        summary = self.billing_repo.get_summary(
            start_date=start_date,
            end_date=end_date,
            provider_id=str(provider_id) if provider_id else None,
        )

        # Get service breakdown
        services = self.billing_repo.get_services_breakdown(
            start_date=start_date,
            end_date=end_date,
            provider_id=str(provider_id) if provider_id else None,
            limit=50,
        )

        # Calculate average cost per record
        avg_cost_per_record = None
        if summary["total_records"] > 0:
            avg_cost_per_record = summary["total_cost"] / summary["total_records"]

        return {
            "total_records": summary["total_records"],
            "total_cost": summary["total_cost"],
            "average_cost_per_record": avg_cost_per_record,
            "cost_by_provider": summary.get("providers", {}),
            "cost_by_service": {
                svc["service_name"]: svc["total_cost"]
                for svc in services
                if svc["service_name"]
            },
            "period_start": start_date,
            "period_end": end_date,
        }

    def get_sync_status(
        self, provider_id: UUID | None = None, limit: int = 10
    ) -> dict[str, Any]:
        """
        Get sync status for providers.

        Args:
            provider_id: Filter by provider
            limit: Number of recent runs

        Returns:
            Sync status information
        """
        runs = self.pipeline_repo.get_recent_pipeline_runs(
            provider_id=str(provider_id) if provider_id is not None else None,
            limit=limit,
        )

        return {
            "runs": runs,
            "summary": self._get_sync_summary(runs),
        }

    def validate_focus_compliance(
        self,
        provider_id: UUID | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Validate FOCUS compliance of billing data.

        Args:
            provider_id: Filter by provider
            start_date: Start of validation period
            end_date: End of validation period

        Returns:
            Validation results
        """
        days_back = 30  # Default to last 30 days if not specified

        start_date, end_date = self._get_date_range(start_date, end_date, days_back)

        # Get sample data from date range
        data, total = self.billing_repo.get_billing_data(
            start_date=start_date,
            end_date=end_date,
            provider_id=str(provider_id) if provider_id else None,
            limit=1000,  # Validate up to 1000 records
        )

        if not data:
            return {
                "status": "no_data",
                "message": "No billing data found to validate",
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "compliance_rate": 100.0,
                "total_records": 0,
                "valid_records": 0,
                "errors": [],
                "warnings": [],
            }

        # Run validation
        validation_results = []
        error_counts = {}
        warning_counts = {}

        for record in data:
            # Convert record to FocusRecord format for validation
            try:
                focus_record = FocusRecord(**self._serialize_billing_record(record))
                validation_result = self.validator.validate_record(focus_record)
                result_dict = validation_result.to_dict()

                if not result_dict["is_valid"] or result_dict["warnings"]:
                    validation_results.append(
                        {
                            "record_id": record.id,
                            "service_name": record.service_name,
                            "charge_period": f"{record.charge_period_start.date()} to {record.charge_period_end.date()}",
                            "errors": [e["message"] for e in result_dict["errors"]],
                            "warnings": [w["message"] for w in result_dict["warnings"]],
                        }
                    )

                    # Count errors by type
                    for error in result_dict["errors"]:
                        error_msg = error["message"]
                        error_counts[error_msg] = error_counts.get(error_msg, 0) + 1

                    # Count warnings by type
                    for warning in result_dict["warnings"]:
                        warning_msg = warning["message"]
                        warning_counts[warning_msg] = (
                            warning_counts.get(warning_msg, 0) + 1
                        )
            except Exception as e:
                # If record doesn't validate as FocusRecord, it's invalid
                error_msg = f"Failed to validate record structure: {str(e)}"
                validation_results.append(
                    {
                        "record_id": record.id,
                        "service_name": record.service_name,
                        "charge_period": f"{record.charge_period_start.date()} to {record.charge_period_end.date()}",
                        "errors": [error_msg],
                        "warnings": [],
                    }
                )
                error_counts[error_msg] = error_counts.get(error_msg, 0) + 1

        # Calculate compliance rate
        valid_records = total - len(validation_results)
        compliance_rate = (valid_records / total * 100) if total > 0 else 100.0

        return {
            "status": "completed",
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "compliance_rate": round(compliance_rate, 2),
            "total_records": total,
            "valid_records": valid_records,
            "invalid_records": len(validation_results),
            "top_errors": sorted(
                error_counts.items(), key=lambda x: x[1], reverse=True
            )[:10],
            "top_warnings": sorted(
                warning_counts.items(), key=lambda x: x[1], reverse=True
            )[:10],
            "validation_details": validation_results[
                :50
            ],  # Return first 50 for details
        }

    def _serialize_billing_record(self, record: BillingData) -> dict[str, Any]:
        """Convert BillingData to dict for API response."""
        return {
            "id": record.id,
            "x_provider_id": record.x_provider_id,
            "provider_name": record.provider_name,
            "publisher_name": record.publisher_name,
            "effective_cost": float(record.effective_cost)
            if record.effective_cost
            else 0,
            "billed_cost": float(record.billed_cost) if record.billed_cost else 0,
            "list_cost": float(record.list_cost) if record.list_cost else 0,
            "contracted_cost": float(record.contracted_cost)
            if record.contracted_cost
            else 0,
            "billing_currency": record.billing_currency,
            "pricing_currency": record.pricing_currency,
            "service_name": record.service_name,
            "service_category": record.service_category,
            "charge_category": record.charge_category,
            "charge_class": record.charge_class,
            "charge_description": record.charge_description,
            "charge_period_start": record.charge_period_start.isoformat()
            if record.charge_period_start
            else None,
            "charge_period_end": record.charge_period_end.isoformat()
            if record.charge_period_end
            else None,
            "billing_period_start": record.billing_period_start.isoformat()
            if record.billing_period_start
            else None,
            "billing_period_end": record.billing_period_end.isoformat()
            if record.billing_period_end
            else None,
            "billing_account_id": record.billing_account_id,
            "billing_account_name": record.billing_account_name,
            "sub_account_id": record.sub_account_id,
            "sub_account_name": record.sub_account_name,
            "resource_id": record.resource_id,
            "resource_name": record.resource_name,
            "resource_type": record.resource_type,
            "sku_id": record.sku_id,
            "sku_price_id": record.sku_price_id,
            "pricing_quantity": float(record.pricing_quantity)
            if record.pricing_quantity
            else None,
            "pricing_unit": record.pricing_unit,
            "list_unit_price": float(record.list_unit_price)
            if record.list_unit_price
            else None,
            "contracted_unit_price": float(record.contracted_unit_price)
            if record.contracted_unit_price
            else None,
            "consumed_quantity": float(record.consumed_quantity)
            if record.consumed_quantity
            else None,
            "consumed_unit": record.consumed_unit,
            "tags": record.tags or {},
            "x_provider_data": record.x_provider_data or {},
            "service_subcategory": record.service_subcategory,
            "charge_frequency": record.charge_frequency,
            "invoice_issuer_name": record.invoice_issuer_name,
            "invoice_id": record.invoice_id,
            "x_created_at": record.x_created_at.isoformat()
            if record.x_created_at
            else None,
            "x_updated_at": record.x_updated_at.isoformat()
            if record.x_updated_at
            else None,
        }

    def _get_sync_summary(self, runs: list[dict[str, Any]]) -> dict[str, Any]:
        """Get summary statistics from pipeline runs."""
        if not runs:
            return {
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "running_runs": 0,
                "success_rate": 0.0,
                "last_run_status": None,
                "last_run_time": None,
            }

        total_runs = len(runs)
        successful_runs = len([r for r in runs if r["status"] == "completed"])
        failed_runs = len([r for r in runs if r["status"] == "failed"])
        running_runs = len([r for r in runs if r["status"] == "running"])

        success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0.0

        # Most recent run
        latest_run = runs[0] if runs else None

        return {
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "failed_runs": failed_runs,
            "running_runs": running_runs,
            "success_rate": round(success_rate, 2),
            "last_run_status": latest_run["status"] if latest_run else None,
            "last_run_time": latest_run["started_at"] if latest_run else None,
        }

    def _get_date_range(
        self,
        start_date: datetime | None,
        end_date: datetime | None,
        days_back: int | None = 30,
    ) -> tuple[datetime, datetime]:
        """Get date range for billing queries."""

        if end_date:
            end_date = end_date.replace(
                hour=0, minute=0, second=0, microsecond=0
            ) + timedelta(days=1)
        else:
            end_date = datetime.now(UTC).replace(
                hour=0, minute=0, second=0, microsecond=0
            ) + timedelta(days=1)

        if not start_date:
            if days_back:
                start_date = end_date - timedelta(days=days_back)
            else:
                start_date = end_date - timedelta(days=8)  # Default 7 days

        return start_date, end_date
