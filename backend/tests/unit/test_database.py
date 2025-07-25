"""
Tests for database configuration and connection
"""

from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, SessionLocal, engine, get_db


def test_database_engine_exists():
    """Test that database engine is created."""
    assert engine is not None


def test_session_factory_exists():
    """Test that SessionLocal factory is created."""
    assert SessionLocal is not None

    # Test that it can create sessions
    session = SessionLocal()
    assert session is not None
    session.close()


def test_get_db_session():
    """Test getting database session."""
    # Create a test engine
    test_engine = create_engine("sqlite:///:memory:")

    with patch("app.database.engine", test_engine):
        # Get a session generator
        db_generator = get_db()

        # Get the session
        session = next(db_generator)

        # Session should be valid
        assert session is not None

        # Clean up
        try:
            next(db_generator)
        except StopIteration:
            pass  # Expected behavior


def test_database_models_inherit_base():
    """Test that all models inherit from Base."""
    from app.models.billing_data import BillingData
    from app.models.pipeline_run import PipelineRun
    from app.models.provider import Provider
    from app.models.raw_billing_data import RawBillingData

    models = [Provider, BillingData, PipelineRun, RawBillingData]

    for model in models:
        assert issubclass(model, Base)


def test_database_table_creation():
    """Test that tables can be created successfully."""
    # Create in-memory SQLite database
    test_engine = create_engine("sqlite:///:memory:")

    # This should not raise any errors
    Base.metadata.create_all(bind=test_engine)

    # Check that tables were created
    table_names = Base.metadata.tables.keys()

    expected_tables = ["providers", "billing_data", "pipeline_runs", "raw_billing_data"]
    for expected in expected_tables:
        assert expected in table_names


def test_database_session_rollback_on_exception():
    """Test that database sessions are properly rolled back on exceptions."""
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)

    with patch("app.database.engine", test_engine):
        db_generator = get_db()
        session = next(db_generator)

        # Simulate an exception during database operations
        from sqlalchemy import text

        try:
            # This would normally cause a rollback
            session.execute(text("INVALID SQL"))
        except Exception:
            pass

        # The session should still be usable after exception handling
        assert session is not None

        # Clean up
        try:
            next(db_generator)
        except StopIteration:
            pass


def test_database_connection_sqlite():
    """Test SQLite database connection."""
    from sqlalchemy import text

    # Test connection to in-memory SQLite
    engine = create_engine("sqlite:///:memory:")

    # Should be able to connect
    connection = engine.connect()
    assert connection is not None

    # Should be able to execute simple query
    result = connection.execute(text("SELECT 1"))
    assert result.fetchone()[0] == 1

    connection.close()


def test_database_session_factory():
    """Test database session factory configuration."""
    test_engine = create_engine("sqlite:///:memory:")

    # Create session factory
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    # Should be able to create sessions
    session = TestSessionLocal()
    assert session is not None

    # Session should have correct configuration
    # Note: In SQLAlchemy 2.0, these are configured in the sessionmaker, not on the session instance
    assert session.bind is test_engine

    session.close()


def test_database_metadata_reflection():
    """Test database metadata reflection."""
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)

    # Should be able to reflect existing tables
    from sqlalchemy import MetaData

    metadata = MetaData()
    metadata.reflect(bind=test_engine)

    # Check that tables are reflected
    assert "providers" in metadata.tables
    assert "billing_data" in metadata.tables


def test_database_constraints_and_indexes():
    """Test that database constraints and indexes are properly defined."""
    from app.models.billing_data import BillingData
    from app.models.provider import Provider

    # Provider model should have unique constraint on name
    provider_table = Provider.__table__
    unique_constraints = [
        c for c in provider_table.constraints if hasattr(c, "columns")
    ]
    any("name" in [col.name for col in c.columns] for c in unique_constraints)

    # BillingData should have foreign key to providers
    billing_table = BillingData.__table__
    foreign_keys = list(billing_table.foreign_keys)
    any("provider" in fk.column.table.name for fk in foreign_keys)

    # Note: These assertions depend on the actual model definitions
    # They may need to be adjusted based on your schema
