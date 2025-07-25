"""
AWS Provider Authentication Module
"""

import logging
from typing import Any

import boto3

from app.models.auth import AuthMethod

logger = logging.getLogger(__name__)


class AWSAuth:
    """Handle authentication for AWS provider."""

    # AWS uses multi-factor auth (access key + secret)
    SUPPORTED_METHODS = [AuthMethod.MULTI_FACTOR]
    DEFAULT_METHOD = AuthMethod.MULTI_FACTOR

    # Auth field definitions for UI
    AUTH_FIELDS = {
        AuthMethod.MULTI_FACTOR: {
            "primary": {
                "required": True,
                "type": "group",
                "description": "AWS Credentials",
                "fields": {
                    "access_key_id": {
                        "required": True,
                        "type": "string",
                        "placeholder": "AKIAIOSFODNN7EXAMPLE",
                        "description": "AWS Access Key ID",
                    },
                    "secret_access_key": {
                        "required": True,
                        "type": "password",
                        "placeholder": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                        "description": "AWS Secret Access Key",
                    },
                    "session_token": {
                        "required": False,
                        "type": "password",
                        "placeholder": "FwoGZXIvYXdzEJr...",
                        "description": "AWS Session Token (optional, for temporary credentials)",
                    },
                },
            },
            "secondary": {
                "required": False,
                "type": "group",
                "description": "IAM Role (optional)",
                "fields": {
                    "role_arn": {
                        "required": False,
                        "type": "string",
                        "placeholder": "arn:aws:iam::123456789012:role/CURAccessRole",
                        "description": "IAM Role ARN to assume",
                    },
                    "external_id": {
                        "required": False,
                        "type": "string",
                        "placeholder": "unique-external-id",
                        "description": "External ID for role assumption",
                    },
                },
            },
        }
    }

    def __init__(self, auth_config: dict[str, Any], region: str = "us-east-1"):
        """Initialize AWS authentication."""
        self.auth_config = auth_config
        self.method = auth_config.get("method", self.DEFAULT_METHOD)
        self.region = region

    def get_credentials(self) -> dict[str, Any]:
        """Get AWS credentials from multi-factor auth config."""
        if self.method != AuthMethod.MULTI_FACTOR:
            raise ValueError(f"Unsupported auth method: {self.method}")

        primary = self.auth_config.get("primary", {})

        credentials = {
            "aws_access_key_id": primary.get("access_key_id"),
            "aws_secret_access_key": primary.get("secret_access_key"),
        }

        # Add session token if provided
        if primary.get("session_token"):
            credentials["aws_session_token"] = primary["session_token"]

        return credentials

    def get_role_config(self) -> dict[str, Any] | None:
        """Get IAM role configuration if provided."""
        if self.method != AuthMethod.MULTI_FACTOR:
            return None

        secondary = self.auth_config.get("secondary", {})

        if secondary.get("role_arn"):
            role_config = {
                "role_arn": secondary["role_arn"],
            }
            if secondary.get("external_id"):
                role_config["external_id"] = secondary["external_id"]
            return role_config

        return None

    def get_boto3_session(self) -> boto3.Session:
        """Create boto3 session with credentials."""
        credentials = self.get_credentials()

        # Filter out None values
        session_params = {k: v for k, v in credentials.items() if v is not None}
        session_params["region_name"] = self.region

        return boto3.Session(**session_params)

    def validate(self) -> None:
        """Validate authentication configuration."""
        if not self.auth_config:
            raise ValueError("Authentication configuration is required")

        if self.method != AuthMethod.MULTI_FACTOR:
            raise ValueError(
                f"AWS only supports {AuthMethod.MULTI_FACTOR} authentication"
            )

        primary = self.auth_config.get("primary", {})

        if not primary.get("access_key_id"):
            raise ValueError("AWS Access Key ID is required")

        if not primary.get("secret_access_key"):
            raise ValueError("AWS Secret Access Key is required")
