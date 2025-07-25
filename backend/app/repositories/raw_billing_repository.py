"""
Raw Billing Data Repository
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.raw_billing_data import RawBillingData
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class RawBillingRepository(BaseRepository[RawBillingData]):
    """Repository for raw billing data operations."""

    def __init__(self, db: Session):
        super().__init__(RawBillingData, db)

    async def create(self, raw_billing: RawBillingData) -> RawBillingData:
        """Create new raw billing record with retry mechanism."""
        max_retries = 3

        for attempt in range(max_retries):
            try:
                self.db.add(raw_billing)
                self.db.commit()
                self.db.refresh(raw_billing)
                return raw_billing

            except IntegrityError as e:
                self.db.rollback()
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Database conflict creating raw billing record, attempt {attempt + 1}, retrying..."
                    )
                    # Generate new UUID to avoid conflicts
                    from uuid import uuid4

                    raw_billing.id = str(uuid4())
                    await asyncio.sleep(0.1 * (attempt + 1))
                    continue
                else:
                    logger.error(
                        f"Error creating raw billing record after {max_retries} attempts: {e}"
                    )
                    raise
            except Exception as e:
                self.db.rollback()
                logger.error(f"Error creating raw billing record: {e}")
                raise

    async def create_batch(
        self, raw_billings: list[RawBillingData]
    ) -> list[RawBillingData]:
        """Create multiple raw billing records in batch with retry mechanism."""
        max_retries = 3

        for attempt in range(max_retries):
            try:
                self.db.add_all(raw_billings)
                self.db.commit()

                # Refresh all objects
                for raw_billing in raw_billings:
                    self.db.refresh(raw_billing)

                return raw_billings

            except IntegrityError as e:
                self.db.rollback()
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Database conflict creating raw billing batch, attempt {attempt + 1}, retrying..."
                    )
                    # Generate new UUIDs for all records
                    from uuid import uuid4

                    for raw_billing in raw_billings:
                        raw_billing.id = str(uuid4())
                    await asyncio.sleep(0.1 * (attempt + 1))
                    continue
                else:
                    logger.error(
                        f"Error creating raw billing records batch after {max_retries} attempts: {e}"
                    )
                    raise
            except Exception as e:
                self.db.rollback()
                logger.error(f"Error creating raw billing records batch: {e}")
                raise

    async def get_by_provider_and_period(
        self,
        provider_id: str,
        start_date: datetime,
        end_date: datetime,
        processed: bool | None = None,
    ) -> list[RawBillingData]:
        """Get raw billing records by provider and period."""
        query = self.db.query(RawBillingData).filter(
            RawBillingData.provider_id == provider_id,
            RawBillingData.period_start >= start_date,
            RawBillingData.period_end <= end_date,
        )

        if processed is not None:
            query = query.filter(RawBillingData.processed == processed)

        return query.order_by(RawBillingData.period_start).all()

    async def get_unprocessed(
        self, provider_id: str | None = None, limit: int | None = None
    ) -> list[RawBillingData]:
        """Get unprocessed raw billing records."""
        query = self.db.query(RawBillingData).filter(not RawBillingData.processed)

        if provider_id:
            query = query.filter(RawBillingData.provider_id == provider_id)

        query = query.order_by(RawBillingData.created_at)

        if limit:
            query = query.limit(limit)

        return query.all()

    async def mark_as_processed(
        self, raw_billing_ids: list[str], processed_at: datetime | None = None
    ) -> int:
        """Mark raw billing records as processed."""
        if not raw_billing_ids:
            return 0

        try:
            updated = (
                self.db.query(RawBillingData)
                .filter(RawBillingData.id.in_(raw_billing_ids))
                .update(
                    {
                        "processed": True,
                        "processed_at": processed_at or datetime.now(UTC),
                    },
                    synchronize_session=False,
                )
            )

            self.db.commit()
            return updated
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error marking records as processed: {e}")
            raise

    async def get_by_pipeline_run(self, pipeline_run_id: str) -> list[RawBillingData]:
        """Get all raw billing records for a pipeline run."""
        return (
            self.db.query(RawBillingData)
            .filter(RawBillingData.pipeline_run_id == pipeline_run_id)
            .order_by(RawBillingData.created_at)
            .all()
        )

    async def get_statistics(
        self,
        provider_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Get statistics about raw billing data."""
        query = self.db.query(
            func.count(RawBillingData.id).label("total_count"),
            func.sum(RawBillingData.records_extracted).label("total_records"),
            func.count(RawBillingData.id)
            .filter(RawBillingData.processed)
            .label("processed_count"),
            func.count(RawBillingData.id)
            .filter(not RawBillingData.processed)
            .label("unprocessed_count"),
            func.min(RawBillingData.period_start).label("earliest_period"),
            func.max(RawBillingData.period_end).label("latest_period"),
        )

        if provider_id:
            query = query.filter(RawBillingData.provider_id == provider_id)

        if start_date:
            query = query.filter(RawBillingData.period_start >= start_date)

        if end_date:
            query = query.filter(RawBillingData.period_end <= end_date)

        result = query.first()

        return {
            "total_count": result.total_count or 0,
            "total_records": result.total_records or 0,
            "processed_count": result.processed_count or 0,
            "unprocessed_count": result.unprocessed_count or 0,
            "earliest_period": result.earliest_period,
            "latest_period": result.latest_period,
        }

    async def get_failed_records(
        self, provider_id: str | None = None, limit: int = 100
    ) -> list[RawBillingData]:
        """Get raw billing records that failed processing."""
        query = self.db.query(RawBillingData).filter(
            not RawBillingData.processed,
            RawBillingData.processing_error.isnot(None),
        )

        if provider_id:
            query = query.filter(RawBillingData.provider_id == provider_id)

        return query.order_by(RawBillingData.created_at.desc()).limit(limit).all()

    async def update_processing_error(
        self,
        raw_billing_id: str,
        error_message: str,
        error_details: dict[str, Any] | None = None,
    ) -> RawBillingData | None:
        """Update processing error for a raw billing record."""
        max_retries = 3

        for attempt in range(max_retries):
            try:
                record = (
                    self.db.query(RawBillingData)
                    .filter(RawBillingData.id == raw_billing_id)
                    .first()
                )

                if record:
                    record.processing_error = error_message

                    self.db.commit()
                    self.db.refresh(record)

                return record

            except IntegrityError as e:
                self.db.rollback()
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Database conflict updating processing error, attempt {attempt + 1}, retrying..."
                    )
                    await asyncio.sleep(0.1 * (attempt + 1))
                    continue
                else:
                    logger.error(
                        f"Error updating processing error after {max_retries} attempts: {e}"
                    )
                    raise
            except Exception as e:
                self.db.rollback()
                logger.error(f"Error updating processing error: {e}")
                raise
