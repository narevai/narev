"""
Generic authentication configuration models for flexible provider authentication.
"""

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AuthMethod(str, Enum):
    """Generic authentication methods."""

    # Basic authentication types
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    BASIC = "basic"

    # OAuth2 flows
    OAUTH2_CLIENT_CREDENTIALS = "oauth2_client_credentials"
    OAUTH2_AUTHORIZATION_CODE = "oauth2_authorization_code"

    # Cloud-specific patterns
    SERVICE_ACCOUNT = "service_account"  # JSON key file (GCP, etc)
    CERTIFICATE = "certificate"  # Cert-based auth
    MANAGED_IDENTITY = "managed_identity"  # Cloud managed identities
    DEFAULT_CREDENTIALS = "default_credentials"  # Default SDK credentials
    CREDENTIALS_FILE = "credentials_file"  # Path to credentials file

    # Advanced patterns
    MULTI_FACTOR = "multi_factor"  # Multiple auth methods
    CUSTOM = "custom"  # Provider-specific implementation


class BaseAuthConfig(BaseModel):
    """Base authentication configuration."""

    model_config = ConfigDict(extra="allow")  # Allow provider-specific fields

    method: AuthMethod


class ApiKeyAuth(BaseAuthConfig):
    """API Key authentication."""

    method: Literal[AuthMethod.API_KEY] = Field(default=AuthMethod.API_KEY)
    key: str = Field(..., description="API key")
    header_name: str = Field(default="X-API-Key", description="Header name for API key")
    prefix: str = Field(default="", description="Prefix for the key (e.g., 'Bearer')")


class BearerTokenAuth(BaseAuthConfig):
    """Bearer token authentication."""

    method: Literal[AuthMethod.BEARER_TOKEN] = Field(default=AuthMethod.BEARER_TOKEN)
    token: str = Field(..., description="Bearer token")
    header_name: str = Field(default="Authorization", description="Header name")
    prefix: str = Field(default="Bearer", description="Token prefix")


class BasicAuth(BaseAuthConfig):
    """HTTP Basic authentication."""

    method: Literal[AuthMethod.BASIC] = Field(default=AuthMethod.BASIC)
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class OAuth2ClientCredentials(BaseAuthConfig):
    """OAuth2 Client Credentials flow."""

    method: Literal[AuthMethod.OAUTH2_CLIENT_CREDENTIALS] = Field(
        default=AuthMethod.OAUTH2_CLIENT_CREDENTIALS
    )
    client_id: str = Field(..., description="OAuth2 client ID")
    client_secret: str = Field(..., description="OAuth2 client secret")
    token_url: str = Field(..., description="Token endpoint URL")
    scope: str | None = Field(default=None, description="OAuth2 scope")
    additional_params: dict[str, Any] = Field(default_factory=dict)

    # Token storage (populated after auth)
    access_token: str | None = Field(default=None, description="Current access token")
    expires_at: int | None = Field(
        default=None, description="Token expiration timestamp"
    )


class OAuth2AuthorizationCode(BaseAuthConfig):
    """OAuth2 Authorization Code flow."""

    method: Literal[AuthMethod.OAUTH2_AUTHORIZATION_CODE] = Field(
        default=AuthMethod.OAUTH2_AUTHORIZATION_CODE
    )
    client_id: str = Field(..., description="OAuth2 client ID")
    client_secret: str = Field(..., description="OAuth2 client secret")
    authorization_url: str = Field(..., description="Authorization endpoint URL")
    token_url: str = Field(..., description="Token endpoint URL")
    redirect_uri: str = Field(..., description="Redirect URI")
    scope: str | None = Field(default=None, description="OAuth2 scope")
    state: str | None = Field(default=None, description="OAuth2 state parameter")

    # Token storage
    access_token: str | None = Field(default=None, description="Current access token")
    refresh_token: str | None = Field(default=None, description="Refresh token")
    expires_at: int | None = Field(
        default=None, description="Token expiration timestamp"
    )


class ServiceAccountAuth(BaseAuthConfig):
    """Service account authentication (JSON key file)."""

    method: Literal[AuthMethod.SERVICE_ACCOUNT] = Field(
        default=AuthMethod.SERVICE_ACCOUNT
    )
    credentials: dict[str, Any] = Field(..., description="Service account credentials")

    # Optional fields for specific providers
    scopes: list[str] | None = Field(default=None, description="Authorization scopes")
    subject: str | None = Field(default=None, description="User to impersonate")

    @model_validator(mode="after")
    def validate_credentials(self):
        """Basic validation - providers can add their own."""
        if not isinstance(self.credentials, dict):
            raise ValueError("Credentials must be a dictionary")
        return self


class CertificateAuth(BaseAuthConfig):
    """Certificate-based authentication."""

    method: Literal[AuthMethod.CERTIFICATE] = Field(default=AuthMethod.CERTIFICATE)

    # Certificate options
    cert_content: str | None = Field(
        default=None, description="Certificate content (PEM)"
    )
    cert_path: str | None = Field(default=None, description="Path to certificate file")
    key_content: str | None = Field(
        default=None, description="Private key content (PEM)"
    )
    key_path: str | None = Field(default=None, description="Path to private key file")
    ca_cert_content: str | None = Field(
        default=None, description="CA certificate content"
    )
    ca_cert_path: str | None = Field(default=None, description="Path to CA certificate")
    passphrase: str | None = Field(default=None, description="Private key passphrase")

    @model_validator(mode="after")
    def validate_cert_config(self):
        """Validate certificate configuration."""
        has_cert = bool(self.cert_content or self.cert_path)
        has_key = bool(self.key_content or self.key_path)

        if not has_cert:
            raise ValueError("Either cert_content or cert_path must be provided")
        if not has_key:
            raise ValueError("Either key_content or key_path must be provided")

        return self


class MultiFactorAuth(BaseAuthConfig):
    """Multiple authentication methods combined."""

    method: Literal[AuthMethod.MULTI_FACTOR] = Field(default=AuthMethod.MULTI_FACTOR)
    primary: dict[str, Any] = Field(..., description="Primary auth method")
    secondary: dict[str, Any] | None = Field(
        default=None, description="Secondary auth method"
    )
    additional: list[dict[str, Any]] = Field(default_factory=list)


class CustomAuth(BaseAuthConfig):
    """Custom provider-specific authentication."""

    method: Literal[AuthMethod.CUSTOM] = Field(default=AuthMethod.CUSTOM)
    auth_type: str = Field(..., description="Provider-specific auth type")
    config: dict[str, Any] = Field(default_factory=dict, description="Custom config")


class ManagedIdentityAuth(BaseAuthConfig):
    """Managed Identity authentication (Azure, AWS, GCP)."""

    method: Literal[AuthMethod.MANAGED_IDENTITY] = Field(
        default=AuthMethod.MANAGED_IDENTITY
    )
    client_id: str | None = Field(
        default=None, description="Client ID for user-assigned identity"
    )
    resource_id: str | None = Field(
        default=None, description="Resource ID for the identity"
    )


class DefaultCredentialsAuth(BaseAuthConfig):
    """Default credentials from environment/SDK."""

    method: Literal[AuthMethod.DEFAULT_CREDENTIALS] = Field(
        default=AuthMethod.DEFAULT_CREDENTIALS
    )
    # No additional fields needed - uses environment


class CredentialsFileAuth(BaseAuthConfig):
    """Credentials file authentication."""

    method: Literal[AuthMethod.CREDENTIALS_FILE] = Field(
        default=AuthMethod.CREDENTIALS_FILE
    )
    file_path: str = Field(..., description="Path to credentials file")
    profile: str | None = Field(
        default=None, description="Profile name in credentials file"
    )


# Union type for all authentication configurations
AuthConfig = (
    ApiKeyAuth
    | BearerTokenAuth
    | BasicAuth
    | OAuth2ClientCredentials
    | OAuth2AuthorizationCode
    | ServiceAccountAuth
    | CertificateAuth
    | MultiFactorAuth
    | CustomAuth
    | ManagedIdentityAuth
    | DefaultCredentialsAuth
    | CredentialsFileAuth
)


# Helper to identify sensitive fields
SENSITIVE_FIELD_PATTERNS = [
    "key",
    "secret",
    "password",
    "token",
    "private_key",
    "passphrase",
    "credentials",
    "cert_content",
    "key_content",
]


def is_sensitive_field(field_name: str) -> bool:
    """Check if a field name indicates sensitive data."""
    field_lower = field_name.lower()
    return any(pattern in field_lower for pattern in SENSITIVE_FIELD_PATTERNS)


def get_sensitive_fields(auth_config: dict[str, Any]) -> list[str]:
    """
    Dynamically identify sensitive fields in auth config.

    Args:
        auth_config: Authentication configuration dict

    Returns:
        List of field paths that contain sensitive data
    """
    sensitive_fields = []

    def _check_dict(d: dict, prefix: str = ""):
        for key, value in d.items():
            field_path = f"{prefix}.{key}" if prefix else key

            if is_sensitive_field(key):
                sensitive_fields.append(field_path)

            # Continue recursion even if current field is sensitive
            # This ensures nested sensitive fields are also found
            if isinstance(value, dict):
                _check_dict(value, field_path)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        _check_dict(item, f"{field_path}[{i}]")

    _check_dict(auth_config)
    return sensitive_fields


def create_auth_config(auth_dict: dict[str, Any]) -> AuthConfig:
    """
    Create appropriate auth config from dictionary.

    Args:
        auth_dict: Authentication configuration dictionary

    Returns:
        Appropriate AuthConfig instance
    """
    method = auth_dict.get("method")

    if not method:
        raise ValueError("Authentication method is required")

    try:
        method_enum = AuthMethod(method)
    except ValueError:
        raise ValueError(f"Unsupported authentication method: {method}") from None

    auth_class_map = {
        AuthMethod.API_KEY: ApiKeyAuth,
        AuthMethod.BEARER_TOKEN: BearerTokenAuth,
        AuthMethod.BASIC: BasicAuth,
        AuthMethod.OAUTH2_CLIENT_CREDENTIALS: OAuth2ClientCredentials,
        AuthMethod.OAUTH2_AUTHORIZATION_CODE: OAuth2AuthorizationCode,
        AuthMethod.SERVICE_ACCOUNT: ServiceAccountAuth,
        AuthMethod.CERTIFICATE: CertificateAuth,
        AuthMethod.MULTI_FACTOR: MultiFactorAuth,
        AuthMethod.CUSTOM: CustomAuth,
        AuthMethod.MANAGED_IDENTITY: ManagedIdentityAuth,
        AuthMethod.DEFAULT_CREDENTIALS: DefaultCredentialsAuth,
        AuthMethod.CREDENTIALS_FILE: CredentialsFileAuth,
    }

    auth_class = auth_class_map.get(method_enum)
    if not auth_class:
        # Fallback to custom auth for unknown methods
        auth_dict["method"] = AuthMethod.CUSTOM
        auth_dict["auth_type"] = method
        return CustomAuth(**auth_dict)

    return auth_class(**auth_dict)
