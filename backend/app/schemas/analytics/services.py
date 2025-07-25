"""
Service-related analytics schemas
"""

from pydantic import BaseModel, Field


class ServiceInfo(BaseModel):
    """Information about a service."""

    service_name: str = Field(..., description="Name of the service")
    provider_name: str = Field(..., description="Name of the provider")
    service_category: str = Field(..., description="Category of the service")


class ServicesSummary(BaseModel):
    """Summary information for available services."""

    total_available_services: int = Field(
        ..., description="Total number of available services"
    )


class AvailableServicesResponse(BaseModel):
    """Response for available services endpoint."""

    status: str = Field(..., description="Response status")
    data: list[ServiceInfo] = Field(
        ..., description="List of available services with details"
    )
    summary: ServicesSummary = Field(..., description="Summary information")
    message: str | None = Field(None, description="Error message if status is error")
