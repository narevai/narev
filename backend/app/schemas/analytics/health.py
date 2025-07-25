"""
Health check schemas
"""

from pydantic import BaseModel, Field


class AnalyticsHealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="healthy", description="Service health status")
    service: str = Field(default="analytics_api", description="Service name")
    timestamp: str = Field(..., description="Current timestamp")
