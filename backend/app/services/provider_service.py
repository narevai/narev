"""
Provider Service Layer
"""

import logging
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.models.auth import get_sensitive_fields
from app.models.provider import Provider, ProviderTestResult
from app.repositories.provider_repository import ProviderRepository
from app.schemas.provider import ProviderTestResult as ProviderTestResultSchema
from app.services.encryption_service import EncryptionService
from providers.registry import ProviderRegistry

logger = logging.getLogger(__name__)


class ProviderService:
    """Service layer for provider operations."""

    def __init__(self, db: Session):
        """Initialize provider service."""
        self.db = db
        self.provider_repo = ProviderRepository(db)
        self.encryption_service = EncryptionService()

    def _encrypt_auth_config(self, auth_config: dict[str, Any]) -> dict[str, Any]:
        """
        Encrypt sensitive fields in auth configuration.

        Args:
            auth_config: Authentication configuration

        Returns:
            Auth config with encrypted sensitive fields
        """
        if not auth_config:
            return auth_config

        encrypted_config = auth_config.copy()
        sensitive_fields = get_sensitive_fields(auth_config)

        for field_path in sensitive_fields:
            # Handle nested fields (e.g., "credentials.private_key")
            parts = field_path.split(".")
            current = encrypted_config

            # Navigate to the parent of the field
            for part in parts[:-1]:
                if part in current:
                    current = current[part]
                else:
                    break

            # Encrypt the field value
            field_name = parts[-1]
            if field_name in current and isinstance(current[field_name], str):
                # Only encrypt if not already encrypted
                value = current[field_name]
                if not self._is_encrypted(value):
                    current[field_name] = self.encryption_service.encrypt(value)

        return encrypted_config

    def _decrypt_auth_config(self, auth_config: dict[str, Any]) -> dict[str, Any]:
        """
        Decrypt sensitive fields in auth configuration.

        Args:
            auth_config: Encrypted auth configuration

        Returns:
            Decrypted auth config
        """
        if not auth_config:
            return auth_config

        decrypted_config = auth_config.copy()
        sensitive_fields = get_sensitive_fields(auth_config)

        for field_path in sensitive_fields:
            parts = field_path.split(".")
            current = decrypted_config

            for part in parts[:-1]:
                if part in current:
                    current = current[part]
                else:
                    break

            field_name = parts[-1]
            if field_name in current and isinstance(current[field_name], str):
                # Only decrypt if actually encrypted
                value = current[field_name]
                if self._is_encrypted(value):
                    current[field_name] = self.encryption_service.decrypt(value)
                # If not encrypted, leave as is (backward compatibility)

        return decrypted_config

    def _is_encrypted(self, value: str) -> bool:
        """
        Check if a string value is encrypted by Fernet.

        Fernet encrypted data is base64 encoded and starts with specific patterns.
        """
        if not value or not isinstance(value, str):
            return False

        # Fernet encrypted data starts with 'gAAAAA' when base64 encoded
        # This is because the Fernet token format has a specific structure
        return value.startswith("gAAAAA")

    def get_all_providers(
        self, provider_type: str | None = None, include_inactive: bool = False
    ) -> list[Provider]:
        """Get all providers."""
        return self.provider_repo.get_all(
            include_inactive=include_inactive, provider_type=provider_type
        )

    def get_provider(self, provider_id: UUID) -> Provider | None:
        """Get provider by ID."""
        return self.provider_repo.get(provider_id)

    async def create_provider(
        self,
        name: str,
        provider_type: str,
        display_name: str | None = None,
        auth_config: dict[str, Any] | None = None,
        api_endpoint: str | None = None,
        additional_config: dict[str, Any] | None = None,
    ) -> Provider:
        """
        Create a new provider with authentication configuration.

        Args:
            name: Unique provider name
            provider_type: Provider type (openai, aws, etc.)
            display_name: Display name
            auth_config: Authentication configuration (required)
            api_endpoint: API endpoint
            additional_config: Additional configuration

        Returns:
            Created provider
        """
        # Validate auth_config is provided
        if not auth_config:
            raise ValueError("Authentication configuration is required")

        # Check if provider already exists
        existing = self.provider_repo.get_by_name(name)
        if existing:
            raise ValueError(f"Provider with name '{name}' already exists")

        # Validate provider type against registry
        supported_types = ProviderRegistry.get_supported_types()
        if provider_type not in supported_types:
            raise ValueError(
                f"Invalid provider type: {provider_type}. "
                f"Supported types: {', '.join(supported_types)}"
            )

        # Get provider metadata from registry
        metadata = ProviderRegistry.get_provider_metadata(provider_type)
        if not metadata:
            raise ValueError(f"No metadata found for provider type: {provider_type}")

        # Validate auth method is supported
        auth_method = auth_config.get("method")
        supported_auth_methods = [
            m.value for m in metadata.get("supported_auth_methods", [])
        ]
        if auth_method not in supported_auth_methods:
            raise ValueError(
                f"Auth method '{auth_method}' not supported for {provider_type}. "
                f"Supported methods: {', '.join(supported_auth_methods)}"
            )

        # Validate required configuration fields
        required_fields = metadata.get("required_config", [])
        config = additional_config or {}

        missing_fields = [field for field in required_fields if not config.get(field)]
        if missing_fields:
            raise ValueError(
                f"Missing required fields for {provider_type}: {', '.join(missing_fields)}"
            )

        # Prepare provider data
        provider_data = {
            "id": str(uuid4()),
            "name": name,
            "provider_type": provider_type,
            "display_name": display_name or metadata.get("display_name", name),
            "api_endpoint": api_endpoint or metadata.get("default_endpoint"),
            "auth_config": self._encrypt_auth_config(auth_config),
            "additional_config": additional_config or {},
            "is_active": True,
            "is_validated": False,
        }

        # Create provider
        provider = self.provider_repo.create(provider_data)

        # Test connection
        try:
            test_result = await self.test_provider_connection(UUID(provider.id))
            if test_result.success:
                self.provider_repo.update(UUID(provider.id), {"is_validated": True})
        except Exception as e:
            logger.warning(f"Failed to test new provider {provider.id}: {e}")

        return provider

    async def update_provider(
        self,
        provider_id: UUID,
        display_name: str | None = None,
        auth_config: dict[str, Any] | None = None,
        api_endpoint: str | None = None,
        additional_config: dict[str, Any] | None = None,
        is_active: bool | None = None,
    ) -> Provider | None:
        """
        Update a provider.

        Args:
            provider_id: Provider ID
            display_name: New display name
            auth_config: New auth configuration
            api_endpoint: New API endpoint
            additional_config: New additional config
            is_active: Active status

        Returns:
            Updated provider or None
        """
        provider = self.provider_repo.get(provider_id)
        if not provider:
            return None

        update_data = {}

        if display_name is not None:
            update_data["display_name"] = display_name

        if auth_config is not None:
            # Validate auth method if provider type is known
            metadata = ProviderRegistry.get_provider_metadata(provider.provider_type)
            if metadata:
                auth_method = auth_config.get("method")
                supported_auth_methods = [
                    m.value for m in metadata.get("supported_auth_methods", [])
                ]
                if auth_method not in supported_auth_methods:
                    raise ValueError(
                        f"Auth method '{auth_method}' not supported for {provider.provider_type}"
                    )

            update_data["auth_config"] = self._encrypt_auth_config(auth_config)
            update_data["is_validated"] = False  # Require revalidation

        if api_endpoint is not None:
            update_data["api_endpoint"] = api_endpoint

        if additional_config is not None:
            update_data["additional_config"] = additional_config

        if is_active is not None:
            update_data["is_active"] = is_active

        return self.provider_repo.update(provider_id, update_data)

    async def delete_provider(self, provider_id: UUID) -> bool:
        """Delete (deactivate) a provider."""
        return self.provider_repo.delete(provider_id)

    async def test_provider_connection(
        self, provider_id: UUID
    ) -> ProviderTestResultSchema:
        """
        Test provider connection with current authentication.

        Args:
            provider_id: Provider ID

        Returns:
            Test result
        """
        provider = self.provider_repo.get(provider_id)
        if not provider:
            return ProviderTestResultSchema(
                success=False,
                message="Provider not found",
                details={"error": "Provider does not exist"},
            )

        try:
            # Get provider configuration with decrypted auth
            config = self.get_provider_config(provider_id)
            if not config:
                raise ValueError("Failed to get provider configuration")

            # Get provider implementation
            provider_class = ProviderRegistry.get_provider_class(provider.provider_type)
            if not provider_class:
                raise ValueError(
                    f"No implementation for provider type: {provider.provider_type}"
                )

            # Create provider instance and test
            provider_instance = provider_class(config)
            result = provider_instance.test_connection()

            # Save test result
            self._save_test_result(
                provider_id=provider_id,
                success=result.get("success", False),
                message=result.get("message", "Connection test completed"),
                details=result,
            )

            return ProviderTestResultSchema(
                success=result.get("success", False),
                message=result.get("message", "Connection test completed"),
                details=result,
            )

        except Exception as e:
            logger.error(f"Provider connection test failed: {e}")

            # Save failed test result
            self._save_test_result(
                provider_id=provider_id,
                success=False,
                message=str(e),
                details={"error": str(e), "type": type(e).__name__},
            )

            return ProviderTestResultSchema(
                success=False,
                message=f"Connection test failed: {str(e)}",
                details={"error": str(e)},
            )

    def _save_test_result(
        self,
        provider_id: UUID,
        success: bool,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> ProviderTestResult:
        """Save provider test result to database."""
        return self.provider_repo.save_test_result(
            provider_id=provider_id,
            is_successful=success,
            message=message,
            details=details,
        )

    def get_provider_config(self, provider_id: UUID) -> dict[str, Any] | None:
        """
        Get provider configuration for pipeline with decrypted auth.

        Args:
            provider_id: Provider ID

        Returns:
            Provider configuration or None
        """
        provider = self.provider_repo.get(provider_id)
        if not provider:
            return None

        config = {
            "id": provider.id,
            "name": provider.name,
            "display_name": provider.display_name,
            "provider_type": provider.provider_type,
            "api_endpoint": provider.api_endpoint,
            **(provider.additional_config or {}),
        }

        # Add decrypted auth configuration
        if provider.auth_config:
            config["auth_config"] = self._decrypt_auth_config(provider.auth_config)

        return config

    def get_provider_types_info(self) -> dict[str, Any]:
        """Get information about all supported provider types."""
        providers_list = []

        for provider_type in ProviderRegistry.get_supported_types():
            metadata = ProviderRegistry.get_provider_metadata(provider_type)
            if metadata:
                # Convert auth methods to AuthMethodInfo objects
                auth_methods = []
                for method in metadata.get("supported_auth_methods", []):
                    method_str = (
                        method.value if hasattr(method, "value") else str(method)
                    )
                    # Get auth fields for this method
                    auth_fields = metadata.get("auth_fields", {}).get(method, {})

                    auth_methods.append(
                        {
                            "method": method_str,
                            "display_name": method_str.replace("_", " ").title(),
                            "description": f"{method_str} authentication method",
                            "fields": auth_fields,
                        }
                    )

                provider_info = {
                    "provider_type": provider_type,
                    "display_name": metadata.get("display_name", provider_type),
                    "description": metadata.get("description", ""),
                    "supported_auth_methods": auth_methods,
                    "default_auth_method": metadata.get("default_auth_method", "").value
                    if metadata.get("default_auth_method")
                    else auth_methods[0]["method"]
                    if auth_methods
                    else "",
                    "required_config": metadata.get("required_config", []),
                    "optional_config": metadata.get("optional_config", []),
                    "configuration_schema": {
                        "field_types": metadata.get("field_types", {}),
                        "field_options": metadata.get("field_options", {}),
                        "field_descriptions": metadata.get("field_descriptions", {}),
                        "field_placeholders": metadata.get("field_placeholders", {}),
                        "standard_fields": metadata.get("standard_fields", {}),
                    },
                    "capabilities": metadata.get("supported_features", []),
                    "status": "active",
                    "version": metadata.get("version", "1.0.0"),
                }
                providers_list.append(provider_info)

        return {
            "total_providers": len(providers_list),
            "providers": providers_list,
            "focus_version": "1.2",
            "api_version": "1.0.0",
        }

    def get_auth_fields(
        self, provider_type: str, auth_method: str | None = None
    ) -> dict:
        """Get authentication field definitions for a provider type."""
        from providers.registry import ProviderRegistry

        metadata = ProviderRegistry.get_provider_metadata(provider_type)
        if not metadata:
            raise ValueError(f"Provider type '{provider_type}' not found")

        # Get auth fields from metadata (set by @register decorator)
        auth_fields = {}
        if metadata.get("auth_fields"):
            # Convert enum keys to string values
            for key, value in metadata["auth_fields"].items():
                # If key is an enum (like AuthMethod.BEARER_TOKEN), get its string value
                field_key = key.value if hasattr(key, "value") else str(key)
                auth_fields[field_key] = value

        # Get supported auth methods and convert enums to strings
        supported_methods = []
        if metadata.get("supported_auth_methods"):
            for method in metadata["supported_auth_methods"]:
                method_str = method.value if hasattr(method, "value") else str(method)
                supported_methods.append(method_str)

        # Get default auth method and convert enum to string
        default_method = metadata.get("default_auth_method")
        if default_method:
            default_method = (
                default_method.value
                if hasattr(default_method, "value")
                else str(default_method)
            )

        # Filter by specific auth method if requested
        if auth_method and auth_method in auth_fields:
            auth_fields = {auth_method: auth_fields[auth_method]}

        return {
            "provider_type": provider_type,
            "supported_auth_methods": supported_methods,
            "default_auth_method": default_method,
            "auth_fields": auth_fields,
        }
