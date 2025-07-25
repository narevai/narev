"""
OpenAI Provider Authentication Module
"""

import logging
from typing import Any

from dlt.sources.helpers.rest_client.auth import BearerTokenAuth

from app.models.auth import AuthMethod

logger = logging.getLogger(__name__)


class OpenAIAuth:
    """Handle authentication for OpenAI provider."""

    # OpenAI only supports Bearer token authentication
    SUPPORTED_METHODS = [AuthMethod.BEARER_TOKEN]
    DEFAULT_METHOD = AuthMethod.BEARER_TOKEN

    # Auth field definitions for UI
    AUTH_FIELDS = {
        AuthMethod.BEARER_TOKEN: {
            "token": {
                "required": True,
                "type": "password",
                "placeholder": "sk-admin...",
                "description": "Your OpenAI Admin API key",
            }
        }
    }

    def __init__(self, auth_config: dict[str, Any]):
        """Initialize OpenAI authentication."""
        self.auth_config = auth_config
        self.method = auth_config.get("method", self.DEFAULT_METHOD)

    def get_dlt_auth(self) -> BearerTokenAuth | None:
        """Get DLT authentication object."""
        token = self.auth_config.get("token", "")
        return BearerTokenAuth(token=token) if token else None

    def get_headers(self) -> dict[str, str]:
        """Get authentication headers."""
        token = self.auth_config.get("token", "")
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

    def validate(self) -> None:
        """Validate authentication configuration."""
        if not self.auth_config:
            raise ValueError("Authentication configuration is required")

        if self.method != AuthMethod.BEARER_TOKEN:
            raise ValueError(
                f"OpenAI only supports {AuthMethod.BEARER_TOKEN} authentication"
            )

        if not self.auth_config.get("token"):
            raise ValueError("Bearer token is required")
