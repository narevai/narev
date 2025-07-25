"""
Billing Data Repository
"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import desc, distinct, func
from sqlalchemy.orm import Session

from app.models.billing_data import BillingData

logger = logging.getLogger(__name__)


class BillingRepository:
    """Repository for billing data operations."""

    def __init__(self, db: Session):
        """Initialize repository."""
        self.db = db

    def get_billing_data(
        self,
        skip: int = 0,
        limit: int = 100,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        provider_id: str | None = None,
        service_category: str | None = None,
        service_name: str | None = None,
        charge_category: str | None = None,
        min_cost: float | None = None,
        max_cost: float | None = None,
        **kwargs,
    ) -> tuple[list[BillingData], int]:
        """
        Get billing records with filters and pagination.

        Returns:
            Tuple of (records, total_count)
        """
        query = self.db.query(BillingData)

        # Apply filters
        if start_date:
            query = query.filter(BillingData.charge_period_start >= start_date)

        if end_date:
            query = query.filter(BillingData.charge_period_end <= end_date)

        if provider_id:
            query = query.filter(BillingData.x_provider_id == provider_id)

        if service_category:
            query = query.filter(BillingData.service_category == service_category)

        if service_name:
            query = query.filter(BillingData.service_name.ilike(f"%{service_name}%"))

        if charge_category:
            query = query.filter(BillingData.charge_category == charge_category)

        if min_cost is not None:
            query = query.filter(BillingData.effective_cost >= min_cost)

        if max_cost is not None:
            query = query.filter(BillingData.effective_cost <= max_cost)

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        records = (
            query.order_by(
                desc(BillingData.charge_period_start), desc(BillingData.effective_cost)
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

        return records, total

    def get_summary(
        self,
        start_date: datetime,
        end_date: datetime,
        provider_id: str | None = None,
        currency: str | None = None,
    ) -> dict[str, Any]:
        """
        Get billing summary with aggregations.

        Returns:
            Summary statistics
        """
        query = self.db.query(
            func.sum(BillingData.effective_cost).label("total_effective_cost"),
            func.sum(BillingData.billed_cost).label("total_billed_cost"),
            func.count(distinct(BillingData.id)).label("record_count"),
            func.count(distinct(BillingData.resource_id)).label("unique_resources"),
            func.count(distinct(BillingData.service_name)).label("unique_services"),
            func.count(distinct(BillingData.x_provider_id)).label("unique_providers"),
        ).filter(
            BillingData.charge_period_start >= start_date,
            BillingData.charge_period_end <= end_date,
        )

        if provider_id:
            query = query.filter(BillingData.x_provider_id == provider_id)

        if currency:
            query = query.filter(BillingData.billing_currency == currency)

        result = query.first()

        # Get currency breakdown if multiple currencies
        currency_query = self.db.query(
            BillingData.billing_currency,
            func.sum(BillingData.effective_cost).label("total"),
        ).filter(
            BillingData.charge_period_start >= start_date,
            BillingData.charge_period_end <= end_date,
        )

        if provider_id:
            currency_query = currency_query.filter(
                BillingData.x_provider_id == provider_id
            )

        currency_breakdown = currency_query.group_by(BillingData.billing_currency).all()

        # Get provider breakdown
        provider_query = self.db.query(
            BillingData.x_provider_id,
            func.sum(BillingData.effective_cost).label("total"),
        ).filter(
            BillingData.charge_period_start >= start_date,
            BillingData.charge_period_end <= end_date,
        )

        if provider_id:
            provider_query = provider_query.filter(
                BillingData.x_provider_id == provider_id
            )

        provider_breakdown = provider_query.group_by(BillingData.x_provider_id).all()

        # Get service breakdown
        service_query = self.db.query(
            BillingData.service_name,
            func.sum(BillingData.effective_cost).label("total"),
        ).filter(
            BillingData.charge_period_start >= start_date,
            BillingData.charge_period_end <= end_date,
        )

        if provider_id:
            service_query = service_query.filter(
                BillingData.x_provider_id == provider_id
            )

        service_breakdown = service_query.group_by(BillingData.service_name).all()

        # Get daily costs
        daily_costs = self.get_daily_costs(start_date, end_date, provider_id)

        return {
            "total_cost": float(result.total_effective_cost or 0),
            "total_records": result.record_count or 0,
            "start_date": start_date,
            "end_date": end_date,
            "currency": "USD",  # Default currency
            "providers": {
                str(prov.x_provider_id): float(prov.total or 0)
                for prov in provider_breakdown
                if prov.x_provider_id
            },
            "services": {
                str(svc.service_name): float(svc.total or 0)
                for svc in service_breakdown
                if svc.service_name
            },
            "daily_costs": daily_costs,
            "total_billed_cost": float(result.total_billed_cost or 0),
            "unique_resources": result.unique_resources or 0,
            "unique_services": result.unique_services or 0,
            "unique_providers": result.unique_providers or 0,
            "currency_breakdown": [
                {"currency": curr.billing_currency, "total": float(curr.total or 0)}
                for curr in currency_breakdown
            ],
        }

    def get_services_breakdown(
        self,
        start_date: datetime,
        end_date: datetime,
        provider_id: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Get cost breakdown by service.

        Returns:
            List of services with costs
        """
        query = self.db.query(
            BillingData.service_name,
            BillingData.service_category,
            func.sum(BillingData.effective_cost).label("total_cost"),
            func.count(distinct(BillingData.id)).label("record_count"),
        ).filter(
            BillingData.charge_period_start >= start_date,
            BillingData.charge_period_end <= end_date,
        )

        if provider_id:
            query = query.filter(BillingData.x_provider_id == provider_id)

        results = (
            query.group_by(BillingData.service_name, BillingData.service_category)
            .order_by(desc("total_cost"))
            .limit(limit)
            .all()
        )

        return [
            {
                "service_name": result.service_name,
                "service_category": result.service_category,
                "total_cost": float(result.total_cost or 0),
                "record_count": result.record_count,
            }
            for result in results
        ]

    def get_top_resources(
        self,
        start_date: datetime,
        end_date: datetime,
        provider_id: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Get top resources by cost.

        Returns:
            List of top resources
        """
        query = self.db.query(
            BillingData.resource_id,
            BillingData.resource_name,
            BillingData.service_name,
            func.sum(BillingData.effective_cost).label("total_cost"),
            func.count(distinct(BillingData.id)).label("record_count"),
        ).filter(
            BillingData.charge_period_start >= start_date,
            BillingData.charge_period_end <= end_date,
            BillingData.resource_id.isnot(None),
        )

        if provider_id:
            query = query.filter(BillingData.x_provider_id == provider_id)

        results = (
            query.group_by(
                BillingData.resource_id,
                BillingData.resource_name,
                BillingData.service_name,
            )
            .order_by(desc("total_cost"))
            .limit(limit)
            .all()
        )

        return [
            {
                "resource_id": result.resource_id,
                "resource_name": result.resource_name,
                "service_name": result.service_name,
                "total_cost": float(result.total_cost or 0),
                "record_count": result.record_count,
            }
            for result in results
        ]

    def get_daily_costs(
        self,
        start_date: datetime,
        end_date: datetime,
        provider_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get daily cost breakdown.

        Args:
            start_date: Start date
            end_date: End date
            provider_id: Optional provider filter

        Returns:
            List of daily costs
        """
        query = self.db.query(
            func.date(BillingData.charge_period_start).label("date"),
            func.sum(BillingData.effective_cost).label("total_cost"),
            func.count(distinct(BillingData.id)).label("record_count"),
        ).filter(
            BillingData.charge_period_start >= start_date,
            BillingData.charge_period_end <= end_date,
        )

        if provider_id:
            query = query.filter(BillingData.x_provider_id == provider_id)

        results = (
            query.group_by(func.date(BillingData.charge_period_start))
            .order_by("date")
            .all()
        )

        return [
            {
                # Handle both string and date objects
                "date": str(result.date) if result.date else None,
                "total_cost": float(result.total_cost or 0),
                "record_count": result.record_count,
            }
            for result in results
        ]

    def get_top_skus(
        self,
        start_date: datetime,
        end_date: datetime,
        provider_id: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Get top SKUs by cost.

        Returns:
            List of top SKUs
        """
        query = self.db.query(
            BillingData.sku_id,
            BillingData.service_name,
            func.sum(BillingData.effective_cost).label("total_cost"),
            func.sum(BillingData.consumed_quantity).label("total_quantity"),
            BillingData.consumed_unit,
            func.count(distinct(BillingData.id)).label("record_count"),
        ).filter(
            BillingData.charge_period_start >= start_date,
            BillingData.charge_period_end <= end_date,
            BillingData.sku_id.isnot(None),
        )

        if provider_id:
            query = query.filter(BillingData.x_provider_id == provider_id)

        results = (
            query.group_by(
                BillingData.sku_id, BillingData.service_name, BillingData.consumed_unit
            )
            .order_by(desc("total_cost"))
            .limit(limit)
            .all()
        )

        return [
            {
                "sku_id": result.sku_id,
                "service_name": result.service_name,
                "total_cost": float(result.total_cost or 0),
                "total_quantity": float(result.total_quantity or 0),
                "consumed_unit": result.consumed_unit,
                "record_count": result.record_count,
            }
            for result in results
        ]

    def create_batch(self, billing_records: list[BillingData]) -> int:
        """
        Create multiple billing records in batch.

        Args:
            billing_records: List of billing records

        Returns:
            Number of records created
        """
        if not billing_records:
            return 0

        try:
            self.db.bulk_save_objects(billing_records)
            self.db.commit()
            return len(billing_records)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating billing records batch: {e}")
            raise

    def get_by_id(self, record_id: str) -> BillingData | None:
        """Get billing record by ID."""
        return self.db.query(BillingData).filter(BillingData.id == record_id).first()

    def update_record(
        self, record_id: str, update_data: dict[str, Any]
    ) -> BillingData | None:
        """Update billing record."""
        record = self.get_by_id(record_id)
        if not record:
            return None

        for key, value in update_data.items():
            if hasattr(record, key):
                setattr(record, key, value)

        self.db.commit()
        self.db.refresh(record)

        return record

    def delete_record(self, record_id: str) -> bool:
        """Delete billing record by ID."""
        record = self.get_by_id(record_id)
        if not record:
            return False

        try:
            self.db.delete(record)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting billing record {record_id}: {e}")
            raise

    def get_by_provider(
        self,
        provider_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int | None = None,
    ) -> list[BillingData]:
        """Get billing records by provider."""
        query = self.db.query(BillingData).filter(
            BillingData.x_provider_id == provider_id
        )

        if start_date:
            query = query.filter(BillingData.charge_period_start >= start_date)

        if end_date:
            query = query.filter(BillingData.charge_period_end <= end_date)

        query = query.order_by(desc(BillingData.charge_period_start))

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_cost_by_period(
        self,
        start_date: datetime,
        end_date: datetime,
        provider_id: str | None = None,
        group_by: str = "day",  # "day", "week", "month"
    ) -> list[dict[str, Any]]:
        """
        Get cost aggregated by time period.

        Args:
            start_date: Start date
            end_date: End date
            provider_id: Optional provider filter
            group_by: Grouping period ("day", "week", "month")

        Returns:
            List of cost data grouped by period
        """
        # Choose date truncation based on group_by
        if group_by == "week":
            date_trunc = func.date_trunc("week", BillingData.charge_period_start)
        elif group_by == "month":
            date_trunc = func.date_trunc("month", BillingData.charge_period_start)
        else:  # day
            date_trunc = func.date(BillingData.charge_period_start)

        query = self.db.query(
            date_trunc.label("period"),
            func.sum(BillingData.effective_cost).label("total_cost"),
            func.count(distinct(BillingData.id)).label("record_count"),
        ).filter(
            BillingData.charge_period_start >= start_date,
            BillingData.charge_period_end <= end_date,
        )

        if provider_id:
            query = query.filter(BillingData.x_provider_id == provider_id)

        results = query.group_by("period").order_by("period").all()

        return [
            {
                "date": result.period.isoformat()
                if hasattr(result.period, "isoformat")
                else str(result.period),
                "cost": float(result.total_cost or 0),
                "record_count": result.record_count,
            }
            for result in results
        ]
