"""
NarevAI Billing Analyzer - Provider Model
"""

from typing import Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.config import get_settings
from app.database import Base

settings = get_settings()


def get_json_field():
    """Get appropriate JSON field type based on database."""
    return JSONB if settings.is_postgres else JSON


class Provider(Base):
    """Provider configuration table with flexible authentication support."""

    __tablename__ = "providers"

    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Provider identification
    name = Column(
        String(100), nullable=False, unique=True
    )  # Unique identifier like 'openai_main'
    provider_type = Column(String(50), nullable=False)  # 'openai', 'aws', 'azure', etc.
    display_name = Column(String(200))  # Human-friendly name for UI

    # Authentication - supporting both old and new systems
    auth_config = Column(get_json_field())  # New flexible auth configuration

    # Configuration
    api_endpoint = Column(String(500))  # Custom endpoint if needed
    additional_config = Column(get_json_field())  # Provider-specific configuration

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_validated = Column(Boolean, default=False)
    last_validation_at = Column(DateTime(timezone=True))
    validation_error = Column(Text)

    # Sync metadata
    last_sync_at = Column(DateTime(timezone=True))
    last_sync_status = Column(String(50))  # 'success', 'failed', 'partial'
    last_sync_error = Column(Text)
    sync_statistics = Column(
        get_json_field()
    )  # Stats like records count, time taken, etc.

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_by = Column(String(255))
    updated_by = Column(String(255))

    # Relationships
    raw_billing_records = relationship(
        "RawBillingData", back_populates="provider", cascade="all, delete-orphan"
    )
    billing_records = relationship(
        "BillingData", back_populates="provider", cascade="all, delete-orphan"
    )
    pipeline_runs = relationship(
        "PipelineRun", back_populates="provider", cascade="all, delete-orphan"
    )
    test_results = relationship(
        "ProviderTestResult", back_populates="provider", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Provider(id={self.id}, name={self.name}, type={self.provider_type}, active={self.is_active})>"

    def get_auth_config(self) -> dict[str, Any] | None:
        """
        Get authentication configuration.

        Returns:
            Authentication configuration dict or None
        """
        # Prefer new auth_config
        if self.auth_config:
            return self.auth_config

        return None

    def set_auth_config(self, auth_config: dict[str, Any]) -> None:
        """
        Set authentication configuration.

        Args:
            auth_config: Authentication configuration dict
        """
        self.auth_config = auth_config

    def to_dict(self, include_sensitive=False):
        """Convert to dictionary for API responses."""
        data = {
            "id": self.id,
            "name": self.name,
            "provider_type": self.provider_type,
            "display_name": self.display_name,
            "api_endpoint": self.api_endpoint,
            "is_active": self.is_active,
            "is_validated": self.is_validated,
            "last_validation_at": self.last_validation_at.isoformat()
            if self.last_validation_at
            else None,
            "last_sync_at": self.last_sync_at.isoformat()
            if self.last_sync_at
            else None,
            "last_sync_status": self.last_sync_status,
            "sync_statistics": self.sync_statistics,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_sensitive:
            data["additional_config"] = self.additional_config

        # Include auth method info (non-sensitive)
        auth_config = self.get_auth_config()
        if auth_config:
            data["auth_method"] = auth_config.get("method", "unknown")
            data["auth_configured"] = True
        else:
            data["auth_configured"] = False

        return data


class ProviderTestResult(Base):
    """Provider connection test results."""

    __tablename__ = "provider_test_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    provider_id = Column(String(36), ForeignKey("providers.id"), nullable=False)

    # Test metadata
    test_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    test_type = Column(
        String(50), nullable=False
    )  # 'connection', 'authentication', 'permissions'

    # Results
    success = Column(Boolean, nullable=False)
    response_time_ms = Column(Integer)
    status_code = Column(Integer)
    error_message = Column(Text)
    test_details = Column(get_json_field())

    # Relationship
    provider = relationship("Provider", back_populates="test_results")

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "provider_id": self.provider_id,
            "test_timestamp": self.test_timestamp.isoformat()
            if self.test_timestamp
            else None,
            "test_type": self.test_type,
            "success": self.success,
            "response_time_ms": self.response_time_ms,
            "status_code": self.status_code,
            "error_message": self.error_message,
            "test_details": self.test_details,
        }
