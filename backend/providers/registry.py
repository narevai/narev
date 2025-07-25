"""
Provider Registry
"""

import importlib
import logging
from pathlib import Path
from typing import Any

from app.models.auth import AuthMethod
from focus.mappers.base import BaseFocusMapper
from pipeline.sources.base import BaseSource
from providers.base import BaseProvider

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """Registry for providers, their mappers and sources."""

    _providers: dict[str, dict[str, Any]] = {}
    _mappers: dict[str, type[BaseFocusMapper]] = {}
    _sources: dict[str, type[BaseSource]] = {}
    _source_types: dict[str, str] = {}  # Default source type for each provider

    @classmethod
    def register(
        cls,
        provider_type: str,
        display_name: str,
        description: str = "",
        supported_features: list[str] | None = None,
        required_config: list[str] | None = None,
        optional_config: list[str] | None = None,
        version: str = "1.0.0",
        mapper_class: type[BaseFocusMapper] | None = None,
        source_class: type[BaseSource] | None = None,
        default_source_type: str = "rest_api",
        # Authentication support
        supported_auth_methods: list[AuthMethod] | None = None,
        default_auth_method: AuthMethod | None = None,
        auth_fields: dict[str, dict[str, Any]] | None = None,
        # Enhanced metadata fields
        default_config: dict[str, Any] | None = None,
        field_descriptions: dict[str, str] | None = None,
        field_types: dict[str, str] | None = None,
        field_placeholders: dict[str, str] | None = None,
        field_options: dict[str, list[dict[str, str]]] | None = None,
        standard_fields: dict[str, dict[str, Any]] | None = None,
        best_practices: list[str] | None = None,
        recommendation_rules: dict[str, Any] | None = None,
    ):
        """
        Enhanced decorator to register a provider with complete metadata.

        Args:
            provider_type: Unique identifier for the provider
            display_name: Human-readable name
            description: Provider description
            supported_features: List of supported features
            required_config: Required configuration fields (go to additional_config)
            optional_config: Optional configuration fields (go to additional_config)
            version: Provider version
            mapper_class: FOCUS mapper class
            source_class: Data source configuration class
            default_source_type: Default source type (rest_api, filesystem, sql_database)
            supported_auth_methods: List of supported authentication methods
            default_auth_method: Default authentication method
            auth_fields: Authentication field definitions per method
            default_config: Default values for configuration fields
            field_descriptions: Descriptions for each field
            field_types: Field types (string, json, password, select, etc.)
            field_placeholders: Placeholder/example values
            field_options: Options for select fields
            standard_fields: Standard form fields (name, display_name, api_key)
            best_practices: List of best practices for this provider
            recommendation_rules: Rules for configuration recommendations
        """

        def decorator(provider_class: type[BaseProvider]) -> type[BaseProvider]:
            if not issubclass(provider_class, BaseProvider):
                raise TypeError(f"{provider_class} must inherit from BaseProvider")

            # Store provider with enhanced metadata
            cls._providers[provider_type] = {
                "class": provider_class,
                "metadata": {
                    "provider_type": provider_type,
                    "display_name": display_name,
                    "description": description,
                    "supported_features": supported_features or [],
                    "required_config": required_config or [],
                    "optional_config": optional_config or [],
                    "version": version,
                    "default_source_type": default_source_type,
                    # Authentication
                    "supported_auth_methods": supported_auth_methods
                    or [AuthMethod.API_KEY],
                    "default_auth_method": default_auth_method or AuthMethod.API_KEY,
                    "auth_fields": auth_fields or {},
                    # Enhanced metadata
                    "default_config": default_config or {},
                    "field_descriptions": field_descriptions or {},
                    "field_types": field_types or {},
                    "field_placeholders": field_placeholders or {},
                    "field_options": field_options or {},
                    "standard_fields": standard_fields or {},
                    "best_practices": best_practices or [],
                    "recommendation_rules": recommendation_rules or {},
                },
            }

            # Store mapper if provided
            if mapper_class:
                if not issubclass(mapper_class, BaseFocusMapper):
                    raise TypeError(f"{mapper_class} must inherit from BaseFocusMapper")
                cls._mappers[provider_type] = mapper_class

            # Store source class if provided
            if source_class:
                if not issubclass(source_class, BaseSource):
                    raise TypeError(f"{source_class} must inherit from BaseSource")
                cls._sources[provider_type] = source_class
                logger.info(f"Registered source class for provider: {provider_type}")

            # Store default source type
            cls._source_types[provider_type] = default_source_type

            logger.info(f"Registered provider: {provider_type}")
            return provider_class

        return decorator

    @classmethod
    def get_provider_class(cls, provider_type: str) -> type[BaseProvider] | None:
        """Get provider class by type."""
        # Try to load provider if not already registered
        if provider_type not in cls._providers:
            cls._load_provider(provider_type)

        provider_info = cls._providers.get(provider_type)
        return provider_info["class"] if provider_info else None

    @classmethod
    def get_mapper_class(cls, provider_type: str) -> type[BaseFocusMapper] | None:
        """Get mapper class by provider type."""
        # Try to load provider if not already registered
        if provider_type not in cls._providers:
            cls._load_provider(provider_type)

        return cls._mappers.get(provider_type)

    @classmethod
    def get_source_class(cls, provider_type: str) -> type[BaseSource] | None:
        """Get source class by provider type."""
        # Try to load provider if not already registered
        if provider_type not in cls._providers:
            cls._load_provider(provider_type)

        return cls._sources.get(provider_type)

    @classmethod
    def get_default_source_type(cls, provider_type: str) -> str:
        """Get default source type for provider."""
        # Try to load provider if not already registered
        if provider_type not in cls._providers:
            cls._load_provider(provider_type)

        return cls._source_types.get(provider_type, "rest_api")

    @classmethod
    def create_provider(
        cls, provider_type: str, config: dict[str, Any]
    ) -> BaseProvider | None:
        """Create provider instance."""
        provider_class = cls.get_provider_class(provider_type)
        if not provider_class:
            logger.error(f"Provider type not found: {provider_type}")
            return None

        # Add provider type to config
        config["provider_type"] = provider_type

        # Create provider instance
        provider_instance = provider_class(config)

        # Add source class to provider instance if available
        source_class = cls.get_source_class(provider_type)
        if source_class:
            provider_instance.source_class = source_class

        return provider_instance

    @classmethod
    def get_mapper(
        cls, provider_type: str, config: dict[str, Any]
    ) -> BaseFocusMapper | None:
        """Create mapper instance."""
        mapper_class = cls.get_mapper_class(provider_type)
        if not mapper_class:
            logger.error(f"No mapper found for provider type: {provider_type}")
            return None

        return mapper_class(config)

    @classmethod
    def get_provider_metadata(cls, provider_type: str) -> dict[str, Any] | None:
        """Get provider metadata with all enhanced fields."""
        # Try to load provider if not already registered
        if provider_type not in cls._providers:
            cls._load_provider(provider_type)

        provider_info = cls._providers.get(provider_type)
        return provider_info["metadata"] if provider_info else None

    @classmethod
    def get_supported_types(cls) -> list[str]:
        """Get list of all supported provider types (registered + available)."""
        registered = set(cls._providers.keys())
        available = set(cls._discover_available_providers())
        return sorted(registered | available)

    @classmethod
    def validate_config(
        cls, provider_type: str, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate provider configuration."""
        metadata = cls.get_provider_metadata(provider_type)
        if not metadata:
            return {
                "valid": False,
                "errors": [f"Unknown provider type: {provider_type}"],
            }

        errors = []

        # Check required fields
        for field in metadata["required_config"]:
            if field not in config or not config[field]:
                errors.append(f"Missing required field: {field}")

        # Check for unknown fields (warnings only)
        all_fields = set(metadata["required_config"] + metadata["optional_config"])
        unknown_fields = (
            set(config.keys())
            - all_fields
            - {
                "provider_type",
                "id",
                "name",
                "display_name",
                "provider_id",
                "auth_config",
            }
        )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": [f"Unknown field: {field}" for field in unknown_fields],
        }

    @classmethod
    def _discover_available_providers(cls) -> list[str]:
        """Discover available provider packages without importing them."""
        try:
            import providers

            providers_path = Path(providers.__file__).parent

            available = []
            for item in providers_path.iterdir():
                if item.is_dir() and not item.name.startswith("_"):
                    # Check if it has provider.py file
                    if (item / "provider.py").exists():
                        available.append(item.name)

            return available
        except Exception as e:
            logger.error(f"Error discovering providers: {e}")
            return []

    @classmethod
    def _load_provider(cls, provider_type: str) -> bool:
        """Load a specific provider module."""
        if provider_type in cls._providers:
            return True  # Already loaded

        try:
            module_name = f"providers.{provider_type}.provider"
            importlib.import_module(module_name)
            logger.debug(f"Loaded provider: {provider_type}")
            return True
        except ImportError as e:
            logger.warning(f"Failed to load provider {provider_type}: {e}")
            return False

    @classmethod
    def clear(cls):
        """Clear registry (for testing)."""
        cls._providers.clear()
        cls._mappers.clear()
        cls._sources.clear()
        cls._source_types.clear()


# Convenience functions
def get_provider(provider_type: str, config: dict[str, Any]) -> BaseProvider | None:
    """Create a configured provider instance."""
    return ProviderRegistry.create_provider(provider_type, config)


def get_mapper(provider_type: str, config: dict[str, Any]) -> BaseFocusMapper | None:
    """Create a configured mapper instance."""
    return ProviderRegistry.get_mapper(provider_type, config)
