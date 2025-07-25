"""
NarevAI Billing Analyzer - Raw Billing Data Model
"""

from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


def get_json_field():
    """Get appropriate JSON field type based on database."""
    from app.config import get_settings

    settings = get_settings()
    return JSONB if settings.is_postgres else JSON


class RawBillingData(Base):
    """
    Raw billing data extracted from various sources.
    Stores data before transformation to FOCUS format.
    """

    __tablename__ = "raw_billing_data"

    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Provider information
    provider_id = Column(String(36), ForeignKey("providers.id"), nullable=False)
    provider_type = Column(String(50), nullable=False)  # 'openai', 'aws', 'gcp', etc.

    # Source information
    source_name = Column(String(255), nullable=False)
    source_type = Column(
        String(50), nullable=False
    )  # e.g., 'rest_api', 'sql_database', 'file'

    # Extraction metadata
    extraction_timestamp = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    extraction_params = Column(get_json_field())  # Any parameters used for extraction

    # Date range for the extracted data
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)

    # The extracted data
    extracted_data = Column(get_json_field(), nullable=False)
    record_count = Column(Integer, default=0)

    # Processing status
    processed = Column(Boolean, default=False, nullable=False)
    processed_at = Column(DateTime(timezone=True))
    processing_error = Column(Text)

    # Pipeline tracking
    pipeline_run_id = Column(String(36))

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    provider = relationship("Provider", back_populates="raw_billing_records")

    # Indexes for performance
    __table_args__ = (
        Index(
            "idx_raw_billing_provider_period",
            "provider_id",
            "period_start",
            "period_end",
        ),
        Index("idx_raw_billing_processed", "processed"),
        Index("idx_raw_billing_created", "created_at"),
        Index("idx_raw_billing_source", "source_name", "source_type"),
        Index("idx_raw_billing_pipeline", "pipeline_run_id"),
    )

    def __repr__(self):
        return f"<RawBillingData(id={self.id}, provider={self.provider_type}, source={self.source_name}, processed={self.processed})>"

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "provider_id": self.provider_id,
            "provider_type": self.provider_type,
            "source_name": self.source_name,
            "source_type": self.source_type,
            "extraction_timestamp": self.extraction_timestamp.isoformat()
            if self.extraction_timestamp
            else None,
            "extraction_params": self.extraction_params,
            "period_start": self.period_start.isoformat()
            if self.period_start
            else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "record_count": self.record_count,
            "processed": self.processed,
            "processed_at": self.processed_at.isoformat()
            if self.processed_at
            else None,
            "processing_error": self.processing_error,
            "pipeline_run_id": self.pipeline_run_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def mark_as_processed(self):
        """Mark record as processed."""
        self.processed = True
        self.processed_at = func.now()
        self.processing_error = None

    def mark_as_failed(self, error_message: str):
        """Mark record as failed."""
        self.processed = True
        self.processed_at = func.now()
        self.processing_error = error_message
