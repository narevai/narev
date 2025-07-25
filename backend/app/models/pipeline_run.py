"""
NarevAI Billing Analyzer - Pipeline Run Model
"""

from uuid import uuid4

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.config import get_settings
from app.database import Base

settings = get_settings()


def get_json_field():
    """Get appropriate JSON field type based on database."""
    return JSONB if settings.is_postgres else JSON


class PipelineRun(Base):
    """Pipeline execution tracking."""

    __tablename__ = "pipeline_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    provider_id = Column(String(36), ForeignKey("providers.id"), nullable=False)

    # Pipeline identification
    pipeline_name = Column(String(255), nullable=False)
    pipeline_version = Column(String(50))
    run_type = Column(String(50), nullable=False)  # 'full', 'incremental', 'backfill'

    # Execution metadata
    status = Column(
        String(50), nullable=False
    )  # 'pending', 'running', 'completed', 'failed', 'cancelled'
    started_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at = Column(DateTime(timezone=True))

    # Stage tracking
    current_stage = Column(String(50))  # 'extract', 'transform', 'load'
    stage_progress = Column(get_json_field())  # Progress per stage

    # Metrics
    records_extracted = Column(Integer, default=0)
    records_transformed = Column(Integer, default=0)
    records_loaded = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)

    # Performance
    duration_seconds = Column(Integer)
    memory_usage_mb = Column(Integer)

    # Error handling
    error_message = Column(Text)
    error_details = Column(get_json_field())
    failed_records = Column(get_json_field())  # Sample of failed records for debugging

    # Configuration used
    pipeline_config = Column(get_json_field())
    date_range_start = Column(DateTime(timezone=True))
    date_range_end = Column(DateTime(timezone=True))

    # DLT specific metadata
    dlt_load_id = Column(String(255))
    dlt_pipeline_state = Column(get_json_field())

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(255))

    # Relationships
    provider = relationship("Provider", back_populates="pipeline_runs")

    # Indexes
    __table_args__ = (
        Index("idx_pipeline_runs_provider_status", "provider_id", "status"),
        Index("idx_pipeline_runs_started", "started_at"),
        Index("idx_pipeline_runs_status", "status"),
    )

    def __repr__(self):
        return f"<PipelineRun(id={self.id}, provider={self.provider_id}, status={self.status}, stage={self.current_stage})>"

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "provider_id": self.provider_id,
            "pipeline_name": self.pipeline_name,
            "pipeline_version": self.pipeline_version,
            "run_type": self.run_type,
            "status": self.status,
            "current_stage": self.current_stage,
            "stage_progress": self.stage_progress,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "duration_seconds": self.duration_seconds,
            "date_range_start": self.date_range_start.isoformat()
            if self.date_range_start
            else None,
            "date_range_end": self.date_range_end.isoformat()
            if self.date_range_end
            else None,
            "metrics": {
                "records_extracted": self.records_extracted,
                "records_transformed": self.records_transformed,
                "records_loaded": self.records_loaded,
                "records_failed": self.records_failed,
            },
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def update_stage(self, stage: str, progress: dict = None):
        """Update current stage and progress."""
        self.current_stage = stage
        if progress:
            if not self.stage_progress:
                self.stage_progress = {}
            self.stage_progress[stage] = progress

    def mark_completed(self, status: str = "completed"):
        """Mark pipeline run as completed."""
        self.status = status
        self.completed_at = func.now()
        if self.started_at and self.completed_at:
            duration = (self.completed_at - self.started_at).total_seconds()
            self.duration_seconds = int(duration)

    def add_error(self, error_message: str, error_details: dict = None):
        """Add error information."""
        self.error_message = error_message
        if error_details:
            self.error_details = error_details
        self.status = "failed"
