"""
Provider API Schemas
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.auth import create_auth_config


class ProviderBase(BaseModel):
    """Base provider schema."""

    name: str = Field(
        ..., description="Unique provider identifier", min_length=1, max_length=100
    )
    provider_type: str = Field(
        ..., description="Provider type (openai, aws, azure, etc.)"
    )
    display_name: str | None = Field(
        None, description="Human-friendly display name", max_length=200
    )
    api_endpoint: str | None = Field(
        None, description="Custom API endpoint", max_length=500
    )
    additional_config: dict[str, Any] | None = Field(
        default_factory=dict, description="Provider-specific configuration"
    )


class ProviderCreate(ProviderBase):
    """Schema for creating a provider with auth configuration."""

    # Auth configuration is required
    auth_config: dict[str, Any] = Field(
        ...,
        description="Authentication configuration",
        example={"method": "bearer_token", "token": "sk-..."},
    )

    @model_validator(mode="after")
    def validate_auth(self):
        """Validate auth_config structure."""
        try:
            create_auth_config(self.auth_config)
        except Exception as e:
            raise ValueError(f"Invalid auth_config: {e}") from e
        return self

    @field_validator("provider_type")
    @classmethod
    def validate_provider_type(cls, v: str) -> str:
        """Validate provider type is supported."""
        from providers.registry import ProviderRegistry

        supported_types = ProviderRegistry.get_supported_types()
        if v not in supported_types:
            raise ValueError(
                f"Provider type must be one of: {', '.join(supported_types)}"
            )
        return v


class ProviderUpdate(BaseModel):
    """Schema for updating a provider."""

    name: str | None = Field(None, min_length=1, max_length=100)
    display_name: str | None = Field(None, max_length=200)

    # Auth configuration
    auth_config: dict[str, Any] | None = Field(
        None, description="Authentication configuration"
    )

    api_endpoint: str | None = Field(None, max_length=500)
    additional_config: dict[str, Any] | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_auth_update(self):
        """Validate auth_config if provided."""
        if self.auth_config:
            try:
                create_auth_config(self.auth_config)
            except Exception as e:
                raise ValueError(f"Invalid auth_config: {e}") from e
        return self


class ProviderResponse(ProviderBase):
    """Schema for provider responses."""

    id: UUID
    is_active: bool
    is_validated: bool
    last_validation_at: datetime | None
    validation_error: str | None
    last_sync_at: datetime | None
    last_sync_status: str | None
    last_sync_error: str | None
    sync_statistics: dict | None
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    updated_by: str | None

    model_config = ConfigDict(from_attributes=True)


class ProviderDetailResponse(ProviderResponse):
    """Detailed provider response with additional info."""

    supported_auth_methods: list[str] = Field(
        default_factory=list, description="List of supported authentication methods"
    )
    validation_error: str | None = Field(None, description="Last validation error")
    sync_statistics: dict[str, Any] | None = Field(None, description="Sync statistics")


class ProviderTestResult(BaseModel):
    """Schema for provider test results."""

    success: bool
    message: str
    details: dict[str, Any] | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ProviderListResponse(BaseModel):
    """Schema for listing providers."""

    providers: list[ProviderResponse]
    total: int
    page: int = 1
    page_size: int = 20


class AuthMethodInfo(BaseModel):
    """Information about an authentication method."""

    method: str = Field(description="Authentication method identifier")
    display_name: str = Field(description="Human-readable name")
    description: str | None = Field(None, description="Method description")
    fields: dict[str, dict[str, Any]] = Field(
        default_factory=dict, description="Field definitions for this auth method"
    )


class ProviderTypeInfo(BaseModel):
    """Information about a provider type."""

    provider_type: str
    display_name: str
    description: str
    supported_auth_methods: list[AuthMethodInfo]
    default_auth_method: str
    required_config: list[str]
    optional_config: list[str]
    configuration_schema: dict[str, Any]
    capabilities: list[str]
    status: str
    version: str


class ProviderTypesResponse(BaseModel):
    """Response for listing provider types."""

    total_providers: int
    providers: list[ProviderTypeInfo]
    focus_version: str
    api_version: str


class AuthFieldConfig(BaseModel):
    required: bool
    type: str
    placeholder: str | None = None
    description: str | None = None
    fields: dict[str, "AuthFieldConfig"] | None = None


class AuthFieldsResponse(BaseModel):
    provider_type: str
    supported_auth_methods: list[str]
    default_auth_method: str
    auth_fields: dict[str, dict[str, AuthFieldConfig]]


class HealthCheckResponse(BaseModel):
    """Health check response for providers API."""

    status: str = Field(..., pattern="^(healthy|unhealthy)$")
    service: str
    version: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str = Field(..., description="Response message")
