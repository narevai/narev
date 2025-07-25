"""
Provider Repository - Data access layer for providers
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.billing_data import BillingData
from app.models.pipeline_run import PipelineRun
from app.models.provider import Provider, ProviderTestResult


class ProviderRepository:
    """Repository for provider data access."""

    def __init__(self, db: Session):
        """
        Initialize repository.

        Args:
            db: Database session
        """
        self.db = db

    def get_all(
        self, include_inactive: bool = False, provider_type: str | None = None
    ) -> list[Provider]:
        """
        Get all providers.

        Args:
            include_inactive: Include inactive providers
            provider_type: Filter by provider type

        Returns:
            List of providers
        """
        query = self.db.query(Provider)

        if not include_inactive:
            query = query.filter(Provider.is_active)

        if provider_type:
            query = query.filter(Provider.provider_type == provider_type)

        return query.order_by(Provider.created_at.desc()).all()

    def get(self, provider_id: UUID) -> Provider | None:
        """
        Get provider by ID.

        Args:
            provider_id: Provider ID

        Returns:
            Provider or None
        """
        return self.db.query(Provider).filter(Provider.id == str(provider_id)).first()

    def get_by_name(self, name: str) -> Provider | None:
        """
        Get provider by name.

        Args:
            name: Provider name

        Returns:
            Provider or None
        """
        return self.db.query(Provider).filter(Provider.name == name).first()

    def create(self, provider_data: dict[str, Any]) -> Provider:
        """
        Create a new provider.

        Args:
            provider_data: Provider data

        Returns:
            Created provider
        """
        provider = Provider(**provider_data)

        self.db.add(provider)
        self.db.commit()
        self.db.refresh(provider)

        return provider

    def update(self, provider_id: UUID, update_data: dict[str, Any]) -> Provider | None:
        """
        Update a provider.

        Args:
            provider_id: Provider ID
            update_data: Fields to update

        Returns:
            Updated provider or None
        """
        provider = self.get(provider_id)
        if not provider:
            return None

        # Update fields
        for key, value in update_data.items():
            if hasattr(provider, key):
                setattr(provider, key, value)

        provider.updated_at = datetime.now(UTC)

        self.db.commit()
        self.db.refresh(provider)

        return provider

    def delete(self, provider_id: UUID) -> bool:
        """
        Delete (deactivate) a provider.

        Args:
            provider_id: Provider ID

        Returns:
            True if successful
        """
        provider = self.get(provider_id)
        if not provider:
            return False

        # Soft delete - just deactivate
        provider.is_active = False
        provider.updated_at = datetime.now(UTC)

        self.db.commit()
        return True

    def has_billing_data(self, provider_id: UUID) -> bool:
        """
        Check if provider has any billing data.

        Args:
            provider_id: Provider ID

        Returns:
            True if billing data exists, False otherwise
        """
        return (
            self.db.query(BillingData)
            .filter(BillingData.x_provider_id == str(provider_id))
            .first()
            is not None
        )

    def get_provider_statistics(self, provider_id: UUID) -> dict[str, Any]:
        """
        Get provider statistics.

        Args:
            provider_id: Provider ID

        Returns:
            Statistics dictionary
        """
        provider = self.get(provider_id)
        if not provider:
            return {}

        # Get pipeline run stats
        pipeline_runs = (
            self.db.query(PipelineRun)
            .filter(PipelineRun.provider_id == str(provider_id))
            .order_by(PipelineRun.started_at.desc())
            .limit(10)
            .all()
        )

        successful_runs = [r for r in pipeline_runs if r.status == "completed"]
        failed_runs = [r for r in pipeline_runs if r.status == "failed"]

        # Calculate average duration
        durations = [r.duration_seconds for r in successful_runs if r.duration_seconds]
        avg_duration = sum(durations) / len(durations) if durations else 0

        # Total records processed
        total_records = sum(r.records_loaded or 0 for r in successful_runs)

        # Get billing record count
        billing_count = (
            self.db.query(func.count(BillingData.id))
            .filter(BillingData.provider_id == str(provider_id))
            .scalar()
        )

        return {
            "provider_id": str(provider_id),
            "is_active": provider.is_active,
            "is_validated": provider.is_validated,
            "last_sync": provider.last_sync_at.isoformat()
            if provider.last_sync_at
            else None,
            "pipeline_runs": {
                "total": len(pipeline_runs),
                "successful": len(successful_runs),
                "failed": len(failed_runs),
                "average_duration_seconds": round(avg_duration, 2),
            },
            "records": {
                "total_processed": total_records,
                "billing_records": billing_count,
            },
        }

    def update_sync_status(
        self,
        provider_id: UUID,
        status: str,
        error: str | None = None,
        statistics: dict[str, Any] | None = None,
    ) -> None:
        """
        Update provider sync status.

        Args:
            provider_id: Provider ID
            status: Sync status
            error: Error message if failed
            statistics: Sync statistics
        """
        provider = self.get(provider_id)
        if not provider:
            return

        provider.last_sync_at = datetime.now(UTC)
        provider.last_sync_status = status
        provider.last_sync_error = error

        if statistics:
            provider.sync_statistics = statistics

        self.db.commit()

    def save_test_result(
        self,
        provider_id: UUID,
        is_successful: bool,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> ProviderTestResult:
        """
        Save provider test result.

        Args:
            provider_id: Provider ID
            is_successful: Test success status
            message: Test message
            details: Additional details

        Returns:
            Test result
        """
        test_result = ProviderTestResult(
            provider_id=str(provider_id),
            test_type="connection",
            success=is_successful,
            error_message=message if not is_successful else None,
            test_details=details or {},
            response_time_ms=details.get("response_time_ms") if details else None,
            status_code=details.get("status_code") if details else None,
        )

        self.db.add(test_result)

        # Update provider validation status
        provider = self.get(provider_id)
        if provider:
            provider.is_validated = is_successful
            provider.last_validation_at = datetime.now(UTC)
            provider.validation_error = message if not is_successful else None

        self.db.commit()
        self.db.refresh(test_result)

        return test_result

    def get_latest_test_result(self, provider_id: UUID) -> ProviderTestResult | None:
        """
        Get latest test result for provider.

        Args:
            provider_id: Provider ID

        Returns:
            Latest test result or None
        """
        return (
            self.db.query(ProviderTestResult)
            .filter(ProviderTestResult.provider_id == str(provider_id))
            .order_by(ProviderTestResult.tested_at.desc())
            .first()
        )

    def get_active_providers_for_sync(self) -> list[Provider]:
        """
        Get all active providers ready for sync.

        Returns:
            List of active providers
        """
        return (
            self.db.query(Provider)
            .filter(and_(Provider.is_active, Provider.is_validated))
            .all()
        )
