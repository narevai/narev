"""
FOCUS Service
"""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.billing_repository import BillingRepository

logger = logging.getLogger(__name__)


class FocusService:
    """Service for FOCUS data operations."""

    def __init__(self, db: Session):
        self.db = db
        self.billing_repo = BillingRepository(db)

    def get_focus_data(
        self,
        skip: int = 0,
        limit: int = 100,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        provider_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Get billing data in FOCUS format."""

        billing_records, total = self.billing_repo.get_billing_data(
            skip=skip,
            limit=limit,
            start_date=start_date,
            end_date=end_date,
            provider_id=str(provider_id) if provider_id else None,
        )

        focus_records = []
        for billing_record in billing_records:
            try:
                focus_record = billing_record.to_focus_record()
                focus_dict = focus_record.to_focus_dict()
                focus_records.append(focus_dict)
            except Exception as e:
                logger.warning(f"Error converting record: {e}")
                continue

        # Calculate pages - always at least 1 page even if no records
        if total == 0:
            pages = 1
        else:
            pages = (total + limit - 1) // limit if limit > 0 else 1

        return {
            "records": focus_records,
            "total": total,
            "page": (skip // limit) + 1 if limit > 0 else 1,
            "pages": pages,
        }
