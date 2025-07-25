"""
Pytest configuration with test database setup
"""

import os
from unittest.mock import Mock, patch

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set encryption key before any imports that might need it
os.environ["ENCRYPTION_KEY"] = Fernet.generate_key().decode()

from app.database import Base

# Import all models to ensure they are registered with Base
# This is critical for Base.metadata.create_all() to work
from app.models.provider import Provider

# Test database configuration
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_db_engine():
    """Create test database engine."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})

    # Force import of all models to ensure they're registered with Base

    # Create all tables
    Base.metadata.create_all(engine)

    # All tables should be created now

    yield engine

    # Clean up
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create test database session."""
    TestSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_db_engine
    )
    session = TestSessionLocal()

    # Create default test provider (many tests need this for foreign keys)
    default_provider = Provider(
        id="provider-1",
        name="test-provider",
        provider_type="openai",
        auth_config={"api_key": "encrypted-key"},
        is_active=True,
    )
    session.add(default_provider)
    session.commit()

    yield session
    session.close()


@pytest.fixture(scope="function")
def test_db_session_clean(test_db_engine):
    """Create clean test database session without any default data."""
    TestSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_db_engine
    )
    session = TestSessionLocal()
    yield session
    session.close()


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    """Mock settings for all tests."""
    from cryptography.fernet import Fernet

    # Create a mock settings object
    mock_settings_obj = Mock()

    # Generate a valid Fernet key for tests
    test_encryption_key = Fernet.generate_key().decode()

    # Set all required attributes
    mock_settings_obj.encryption_key = test_encryption_key
    mock_settings_obj.api_title = "Test API"
    mock_settings_obj.api_description = "Test Description"
    mock_settings_obj.api_version = "1.0.0"
    mock_settings_obj.debug = True
    mock_settings_obj.environment = "test"
    mock_settings_obj.cors_origins = ["http://localhost:3000"]
    mock_settings_obj.cors_origins_list = ["http://localhost:3000"]
    mock_settings_obj.is_development = True
    mock_settings_obj.log_level = "DEBUG"
    mock_settings_obj.log_to_file = False  # Disable file logging in tests
    mock_settings_obj.log_file_path = (
        "/tmp/test.log"  # Provide a valid path even though not used
    )
    mock_settings_obj.database_type = "sqlite"
    mock_settings_obj.sqlite_path = ":memory:"
    mock_settings_obj.database_url = TEST_DATABASE_URL
    mock_settings_obj.is_sqlite = True
    mock_settings_obj.is_postgres = False
    mock_settings_obj.host = "127.0.0.1"
    mock_settings_obj.port = 8000
    mock_settings_obj.database_config = {}

    # Patch both the settings object and get_settings function
    monkeypatch.setattr("app.config.settings", mock_settings_obj)
    monkeypatch.setattr("app.config.get_settings", lambda: mock_settings_obj)

    # Also patch settings in other modules that import it directly
    monkeypatch.setattr("app.database.settings", mock_settings_obj)
    # Patch get_settings function in encryption service
    monkeypatch.setattr(
        "app.services.encryption_service.get_settings", lambda: mock_settings_obj
    )

    # Set encryption key environment variable for services that use it directly
    monkeypatch.setenv("ENCRYPTION_KEY", test_encryption_key)

    yield mock_settings_obj


@pytest.fixture
def client(test_db_session):
    """Test client for API tests."""
    # Import here to avoid circular imports and after mocks are set up
    from fastapi.testclient import TestClient

    from app.database import get_db
    from main import app

    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def client_clean(test_db_session_clean):
    """Test client for API tests with clean database (no default data)."""
    from fastapi.testclient import TestClient

    from app.database import get_db
    from main import app

    def override_get_db():
        try:
            yield test_db_session_clean
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# Fixtures for commonly used test data
@pytest.fixture
def sample_provider_data():
    """Sample provider data for tests."""
    return {
        "id": "test-provider-1",
        "name": "test-openai",
        "provider_type": "openai",
        "display_name": "Test OpenAI Provider",
        "auth_config": {"api_key": "encrypted-test-key"},
        "api_endpoint": "https://api.test.com",
        "is_active": True,
        "is_validated": True,
        "additional_config": {"organization_id": "org-test123"},
    }


@pytest.fixture
def sample_billing_data():
    """Sample billing data for tests."""
    from datetime import UTC, datetime, timedelta
    from decimal import Decimal

    now = datetime.now(UTC)
    return {
        "id": "billing-test-1",
        "x_provider_id": "provider-1",
        "provider_name": "OpenAI",
        "publisher_name": "OpenAI",
        "invoice_issuer_name": "OpenAI",
        "billed_cost": Decimal("10.50"),
        "effective_cost": Decimal("10.50"),
        "list_cost": Decimal("12.00"),
        "contracted_cost": Decimal("10.50"),
        "billing_account_id": "account-1",
        "billing_account_name": "Test Account",
        "billing_account_type": "cloud",  # Add missing required field
        "billing_period_start": now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        ),
        "billing_period_end": (
            now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            + timedelta(days=30)
        ),
        "charge_period_start": now,
        "charge_period_end": now + timedelta(hours=1),
        "billing_currency": "USD",
        "service_name": "GPT-4",
        "service_category": "AI and Machine Learning",
        "charge_category": "Usage",
        "charge_description": "GPT-4 API usage",
        "sku_id": "gpt-4-tokens",
        "consumed_quantity": Decimal("1000"),
        "consumed_unit": "tokens",
    }


@pytest.fixture
def mock_encryption_service():
    """Mock encryption service for tests that need it."""
    from cryptography.fernet import Fernet

    # Generate a valid test key
    test_key = Fernet.generate_key()

    with patch("app.services.encryption_service.EncryptionService") as mock_service:
        instance = mock_service.return_value
        fernet = Fernet(test_key)

        # Mock encrypt method
        def mock_encrypt(text):
            if not text:
                return ""
            return fernet.encrypt(text.encode()).decode()

        # Mock decrypt method
        def mock_decrypt(text):
            if not text:
                return ""

            return fernet.decrypt(text.encode()).decode()

        instance.encrypt = mock_encrypt
        instance.decrypt = mock_decrypt
        instance._fernet = fernet

        yield instance
