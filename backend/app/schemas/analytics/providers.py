"""
Provider-related analytics schemas
"""

from pydantic import BaseModel, Field


class ProvidersSummary(BaseModel):
    """Summary information for connected providers."""

    total_connected_providers: int = Field(
        ..., description="Total number of connected providers"
    )
    provider_list: list[str] = Field(
        ..., description="Sorted list of connected provider names"
    )


class ConnectedProvidersResponse(BaseModel):
    """Response for connected providers endpoint."""

    status: str = Field(..., description="Response status")
    data: list[str] = Field(..., description="List of connected provider names")
    summary: ProvidersSummary = Field(..., description="Summary information")
    message: str | None = Field(None, description="Error message if status is error")
