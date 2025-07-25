"""
Base analytics schemas
"""

from typing import Any

from pydantic import BaseModel, Field


class UseCaseMetadata(BaseModel):
    """Metadata for a single use case."""

    name: str = Field(..., description="Name of the use case")
    endpoint: str = Field(..., description="API endpoint path")
    method: str = Field(default="GET", description="HTTP method")
    status: str = Field(
        ...,
        description="Implementation status",
        pattern="^(not_implemented|in_progress|implemented)$",
    )
    context: str = Field(default="", description="Use case context/description")
    related_personas: list[str] = Field(
        default_factory=list, description="Related FinOps personas"
    )
    related_capabilities: list[str] = Field(
        default_factory=list, description="Related FinOps capabilities"
    )
    focus_columns: list[str] = Field(
        default_factory=list, description="FOCUS columns used"
    )
    example_filters: dict[str, Any] = Field(
        default_factory=dict, description="Example query parameters"
    )


class UseCaseListItem(BaseModel):
    """Single use case in the list."""

    id: str = Field(..., description="Use case identifier")
    endpoint: str = Field(..., description="API endpoint path")
    name: str = Field(..., description="Name of the use case")
    context: str = Field(default="", description="Use case context/description")
    related_personas: list[str] = Field(default_factory=list)
    related_capabilities: list[str] = Field(default_factory=list)
    status: str = Field(..., description="Implementation status")


class UseCaseFilters(BaseModel):
    """Available filters for use cases."""

    available_personas: list[str] = Field(..., description="All available personas")
    available_capabilities: list[str] = Field(
        ..., description="All available capabilities"
    )
    applied_filters: dict[str, str | None] = Field(
        ..., description="Currently applied filters"
    )


class UseCaseListResponse(BaseModel):
    """Response for use case listing."""

    use_cases: list[UseCaseListItem] = Field(..., description="List of use cases")
    total: int = Field(..., description="Total number of use cases")
    filters: UseCaseFilters = Field(..., description="Filter information")


class NotImplementedResponse(BaseModel):
    """Response for not implemented endpoints."""

    status: str = Field(default="not_implemented", description="Implementation status")
    metadata: UseCaseMetadata = Field(..., description="Use case metadata")
    message: str = Field(
        default="This endpoint is not implemented yet", description="Status message"
    )
