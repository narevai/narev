"""
Tests for application configuration
"""

import os
from unittest.mock import patch

from app.config import get_settings


def test_get_settings_default():
    """Test getting settings with default values."""
    with patch.dict(os.environ, {}, clear=True):
        settings = get_settings()

        assert settings.api_title == "NarevAI Billing Analyzer"
        assert settings.api_version == "0.1.0"
        assert settings.environment == "production"
        assert settings.debug is False  # Default is False
        assert settings.database_type == "sqlite"
        assert settings.log_level == "INFO"


def test_get_settings_from_env():
    """Test getting settings from environment variables."""
    # Clear cache before test
    get_settings.cache_clear()

    env_vars = {
        "API_TITLE": "Custom API",
        "API_VERSION": "2.0.0",
        "ENVIRONMENT": "production",
        "DEBUG": "false",
        "DATABASE_TYPE": "sqlite",
        "LOG_LEVEL": "ERROR",
        "SQLITE_PATH": "./test.db",
        "ENCRYPTION_KEY": "test-encryption-key-32-characters",
        "CORS_ORIGINS": "https://app.example.com,https://admin.example.com",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        settings = get_settings()

        assert settings.api_title == "Custom API"
        assert settings.api_version == "2.0.0"
        assert settings.environment == "production"
        assert settings.debug is False
        assert settings.database_type == "sqlite"
        assert settings.log_level == "ERROR"
        assert settings.encryption_key == "test-encryption-key-32-characters"


def test_settings_cors_origins_parsing():
    """Test CORS origins parsing from string to list."""
    # Clear cache before test
    get_settings.cache_clear()

    with patch.dict(
        os.environ,
        {
            "CORS_ORIGINS": "http://localhost:3000,https://app.com",
            "ENCRYPTION_KEY": "test-encryption-key-32-characters",
        },
        clear=True,
    ):
        settings = get_settings()

        assert settings.cors_origins == ["http://localhost:3000", "https://app.com"]
        assert settings.cors_origins_list == [
            "http://localhost:3000",
            "https://app.com",
        ]


def test_settings_boolean_parsing():
    """Test boolean environment variable parsing."""
    # Test various ways to specify True
    for true_value in ["true", "True", "TRUE", "1"]:
        get_settings.cache_clear()  # Clear cache for each test
        with patch.dict(
            os.environ,
            {
                "DEBUG": true_value,
                "ENCRYPTION_KEY": "test-encryption-key-32-characters",
            },
            clear=True,
        ):
            settings = get_settings()
            assert settings.debug is True

    # Test various ways to specify False
    for false_value in ["false", "False", "FALSE", "0"]:
        get_settings.cache_clear()  # Clear cache for each test
        with patch.dict(
            os.environ,
            {
                "DEBUG": false_value,
                "ENCRYPTION_KEY": "test-encryption-key-32-characters",
            },
            clear=True,
        ):
            settings = get_settings()
            assert settings.debug is False


def test_settings_database_properties():
    """Test database-related computed properties."""
    # Clear cache before testing
    get_settings.cache_clear()

    # SQLite
    with patch.dict(
        os.environ,
        {
            "DATABASE_TYPE": "sqlite",
            "ENCRYPTION_KEY": "test-encryption-key-32-characters",
        },
        clear=True,
    ):
        settings = get_settings()
        assert settings.is_sqlite is True
        assert settings.is_postgres is False
        get_settings.cache_clear()  # Clear for next test

    # Test invalid database type (postgres not supported yet)
    with patch.dict(
        os.environ,
        {
            "DATABASE_TYPE": "postgres",
            "ENCRYPTION_KEY": "test-encryption-key-32-characters",
        },
        clear=True,
    ):
        try:
            settings = get_settings()
            raise AssertionError(
                "Expected ValidationError for unsupported database type"
            )
        except Exception as e:
            assert "postgres support coming soon" in str(e)


def test_settings_development_properties():
    """Test development-related computed properties."""
    # Clear cache before testing
    get_settings.cache_clear()

    # Development environment
    with patch.dict(
        os.environ,
        {
            "ENVIRONMENT": "development",
            "ENCRYPTION_KEY": "test-encryption-key-32-characters",
        },
        clear=True,
    ):
        settings = get_settings()
        assert settings.is_development is True
        assert settings.is_production is False
        get_settings.cache_clear()  # Clear for next test

    # Production environment with required encryption key
    with patch.dict(
        os.environ,
        {
            "ENVIRONMENT": "production",
            "ENCRYPTION_KEY": "test-encryption-key-32-characters",
        },
        clear=True,
    ):
        settings = get_settings()
        assert settings.is_development is False
        assert settings.is_production is True


def test_settings_sqlite_path():
    """Test SQLite path configuration."""
    # Clear cache before testing
    get_settings.cache_clear()

    # Default SQLite path
    with patch.dict(
        os.environ,
        {
            "DATABASE_TYPE": "sqlite",
            "ENCRYPTION_KEY": "test-encryption-key-32-characters",
        },
        clear=True,
    ):
        settings = get_settings()
        assert settings.sqlite_path == "./data/billing.db"
        get_settings.cache_clear()  # Clear for next test

    # Custom SQLite path
    with patch.dict(
        os.environ,
        {
            "DATABASE_TYPE": "sqlite",
            "SQLITE_PATH": "/custom/path/custom.db",
            "ENCRYPTION_KEY": "test-encryption-key-32-characters",
        },
        clear=True,
    ):
        settings = get_settings()
        assert settings.sqlite_path == "/custom/path/custom.db"


def test_settings_host_and_port():
    """Test host and port configuration."""
    get_settings.cache_clear()

    # Default values
    with patch.dict(
        os.environ,
        {"ENCRYPTION_KEY": "test-encryption-key-32-characters"},
        clear=True,
    ):
        settings = get_settings()
        assert settings.host == "0.0.0.0"
        assert settings.port == 8000
        get_settings.cache_clear()

    # Custom values
    with patch.dict(
        os.environ,
        {
            "HOST": "127.0.0.1",
            "PORT": "8000",
            "ENCRYPTION_KEY": "test-encryption-key-32-characters",
        },
        clear=True,
    ):
        settings = get_settings()
        assert settings.host == "127.0.0.1"
        assert settings.port == 8000


def test_settings_encryption_key_validation():
    """Test encryption key validation."""
    get_settings.cache_clear()

    # Valid key length (32 characters)
    with patch.dict(os.environ, {"ENCRYPTION_KEY": "a" * 32}, clear=True):
        settings = get_settings()
        assert len(settings.encryption_key) == 32
        get_settings.cache_clear()

    # Test encryption key is required - this should raise ValidationError
    with patch.dict(os.environ, {}, clear=True):
        try:
            settings = get_settings()
            raise AssertionError("Expected ValidationError for missing encryption key")
        except Exception as e:
            assert "Encryption key is required" in str(e)


def test_settings_caching():
    """Test that settings are cached using lru_cache."""
    # Clear any existing cache
    get_settings.cache_clear()

    # First call
    settings1 = get_settings()

    # Second call should return same instance (cached)
    settings2 = get_settings()

    assert settings1 is settings2


def test_settings_validation():
    """Test settings validation."""
    # Test with invalid database type
    with patch.dict(
        os.environ,
        {
            "DATABASE_TYPE": "invalid",
            "ENCRYPTION_KEY": "test-encryption-key-32-characters",
        },
        clear=True,
    ):
        settings = get_settings()
        # Should default to sqlite for invalid type
        assert settings.database_type == "sqlite"

    # Test with invalid log level
    with patch.dict(
        os.environ,
        {
            "LOG_LEVEL": "INVALID",
            "ENCRYPTION_KEY": "test-encryption-key-32-characters",
        },
        clear=True,
    ):
        settings = get_settings()
        # Should default to INFO for invalid level
        assert settings.log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def test_settings_postgres_url_construction():
    """Test that PostgreSQL configuration fails as expected (not supported yet)."""
    get_settings.cache_clear()

    env_vars = {
        "DATABASE_TYPE": "postgres",
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_DB": "testdb",
        "POSTGRES_USER": "testuser",
        "POSTGRES_PASSWORD": "testpass",
        "ENCRYPTION_KEY": "test-encryption-key-32-characters",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        try:
            get_settings()
            raise AssertionError(
                "Expected ValidationError for unsupported postgres database type"
            )
        except Exception as e:
            assert "postgres support coming soon" in str(e)


def test_settings_cors_origins_default():
    """Test default CORS origins."""
    get_settings.cache_clear()

    with patch.dict(
        os.environ,
        {"ENCRYPTION_KEY": "test-encryption-key-32-characters"},
        clear=True,
    ):
        settings = get_settings()

        # Should include localhost development origins
        assert "http://localhost:3000" in settings.cors_origins_list
        assert "http://localhost:8000" in settings.cors_origins_list
        assert len(settings.cors_origins_list) == 2


def test_settings_api_description():
    """Test API description configuration."""
    get_settings.cache_clear()

    # Default description
    with patch.dict(
        os.environ,
        {"ENCRYPTION_KEY": "test-encryption-key-32-characters"},
        clear=True,
    ):
        settings = get_settings()
        assert (
            settings.api_description
            == "FOCUS 1.2 compliant billing data analyzer for cloud and SaaS providers"
        )
        get_settings.cache_clear()

    # Custom description
    with patch.dict(
        os.environ,
        {
            "API_DESCRIPTION": "Custom API Description",
            "ENCRYPTION_KEY": "test-encryption-key-32-characters",
        },
        clear=True,
    ):
        settings = get_settings()
        assert settings.api_description == "Custom API Description"


def test_settings_computed_properties_consistency():
    """Test that computed properties are consistent."""
    settings = get_settings()

    # is_development should be opposite of is_production
    assert settings.is_development != settings.is_production

    # Database type properties should be mutually exclusive (currently only sqlite supported)
    assert settings.is_sqlite is True
    assert settings.is_postgres is False
