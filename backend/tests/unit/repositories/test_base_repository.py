"""
Tests for BaseRepository
"""

from datetime import UTC, datetime

import pytest
from sqlalchemy import Column, DateTime, Integer, String, create_engine, orm
from sqlalchemy.orm import sessionmaker

from app.repositories.base import BaseRepository

# Create test model
Base = orm.declarative_base()


class SampleModel(Base):
    """Sample model for repository tests."""

    __tablename__ = "sample_model"

    id = Column(String, primary_key=True)
    name = Column(String)
    value = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(UTC))


@pytest.fixture
def db_session():
    """Create test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_repository(db_session):
    """Create test repository instance."""
    return BaseRepository(SampleModel, db_session)


@pytest.fixture
def sample_records(db_session):
    """Create sample test records."""
    records = []
    for i in range(5):
        record = SampleModel(id=f"test-{i}", name=f"Test {i}", value=i * 10)
        records.append(record)
        db_session.add(record)
    db_session.commit()
    return records


class TestBaseRepository:
    """Test cases for BaseRepository."""

    def test_get_by_id(self, test_repository, sample_records):
        """Test getting record by ID."""
        # Get existing record
        record = test_repository.get("test-0")
        assert record is not None
        assert record.id == "test-0"
        assert record.name == "Test 0"

        # Get non-existent record
        record = test_repository.get("non-existent")
        assert record is None

    def test_get_all_no_filters(self, test_repository, sample_records):
        """Test getting all records without filters."""
        records = test_repository.get_all()

        assert len(records) == 5
        assert all(record.id.startswith("test-") for record in records)

    def test_get_all_with_pagination(self, test_repository, sample_records):
        """Test getting records with pagination."""
        # First page
        records = test_repository.get_all(skip=0, limit=2)
        assert len(records) == 2

        # Second page
        records = test_repository.get_all(skip=2, limit=2)
        assert len(records) == 2

        # Last page
        records = test_repository.get_all(skip=4, limit=2)
        assert len(records) == 1

    def test_get_all_with_ordering(self, test_repository, sample_records):
        """Test getting records with ordering."""
        # Order by value descending (default)
        records = test_repository.get_all(order_by="value", order_desc=True)
        assert records[0].value == 40  # Highest value
        assert records[-1].value == 0  # Lowest value

        # Order by value ascending
        records = test_repository.get_all(order_by="value", order_desc=False)
        assert records[0].value == 0  # Lowest value
        assert records[-1].value == 40  # Highest value

        # Order by name
        records = test_repository.get_all(order_by="name", order_desc=False)
        assert records[0].name == "Test 0"
        assert records[-1].name == "Test 4"

    def test_create(self, test_repository, db_session):
        """Test creating new record."""
        new_record = SampleModel(id="new-test", name="New Test", value=100)

        created_record = test_repository.create(new_record)

        assert created_record.id == "new-test"
        assert created_record.name == "New Test"
        assert created_record.value == 100
        assert created_record.created_at is not None

        # Verify it was saved
        saved_record = test_repository.get("new-test")
        assert saved_record is not None

    def test_update(self, test_repository, sample_records):
        """Test updating existing record."""
        update_data = {"name": "Updated Test", "value": 999}

        updated_record = test_repository.update("test-0", update_data)

        assert updated_record is not None
        assert updated_record.name == "Updated Test"
        assert updated_record.value == 999
        assert updated_record.updated_at is not None

        # Update non-existent record
        updated_record = test_repository.update("non-existent", update_data)
        assert updated_record is None

    def test_update_with_timestamp(self, test_repository, sample_records):
        """Test that update sets updated_at timestamp."""
        original_record = test_repository.get("test-0")
        original_updated_at = original_record.updated_at

        # Wait a bit to ensure timestamp difference
        import time

        time.sleep(0.01)

        updated_record = test_repository.update("test-0", {"name": "Updated"})

        # Updated_at should be newer
        assert updated_record.updated_at > original_updated_at

    def test_delete(self, test_repository, sample_records):
        """Test deleting record."""
        # Delete existing record
        success = test_repository.delete("test-0")
        assert success is True

        # Verify it's deleted
        record = test_repository.get("test-0")
        assert record is None

        # Try to delete non-existent record
        success = test_repository.delete("non-existent")
        assert success is False

    def test_count_no_filters(self, test_repository, sample_records):
        """Test counting records without filters."""
        count = test_repository.count()
        assert count == 5

    def test_count_with_filters(self, test_repository, sample_records):
        """Test counting records with filters."""
        # Count by name
        count = test_repository.count(name="Test 0")
        assert count == 1

        # Count by value
        count = test_repository.count(value=20)
        assert count == 1

        # Count with multiple filters
        count = test_repository.count(name="Test 1", value=10)
        assert count == 1

        # Count with non-matching filters
        count = test_repository.count(name="Non-existent")
        assert count == 0

    def test_exists(self, test_repository, sample_records):
        """Test checking if record exists."""
        # Check existing record
        exists = test_repository.exists(id="test-0")
        assert exists is True

        # Check by other field
        exists = test_repository.exists(name="Test 2")
        assert exists is True

        # Check non-existent
        exists = test_repository.exists(id="non-existent")
        assert exists is False

    def test_bulk_create(self, test_repository, db_session):
        """Test creating multiple records in bulk."""
        new_records = []
        for i in range(3):
            record = SampleModel(id=f"bulk-{i}", name=f"Bulk {i}", value=i * 100)
            new_records.append(record)

        created_records = test_repository.bulk_create(new_records)

        assert len(created_records) == 3
        assert all(record.id.startswith("bulk-") for record in created_records)

        # Verify all were saved
        count = test_repository.count()
        assert count == 3

        # Verify individual records
        for i in range(3):
            record = test_repository.get(f"bulk-{i}")
            assert record is not None
            assert record.name == f"Bulk {i}"
            assert record.value == i * 100

    def test_bulk_update(self, test_repository, sample_records):
        """Test updating multiple records in bulk."""
        updates = [
            {"id": "test-0", "name": "Bulk Updated 0", "value": 1000},
            {"id": "test-1", "name": "Bulk Updated 1", "value": 2000},
            {"id": "test-2", "name": "Bulk Updated 2", "value": 3000},
        ]

        updated_count = test_repository.bulk_update(updates)

        assert updated_count == 3

        # Verify updates
        for i in range(3):
            record = test_repository.get(f"test-{i}")
            assert record.name == f"Bulk Updated {i}"
            assert record.value == (i + 1) * 1000

    def test_bulk_update_with_missing_id(self, test_repository, sample_records):
        """Test bulk update skips records without ID."""
        updates = [
            {"id": "test-0", "name": "Updated"},
            {"name": "No ID"},  # Missing ID
            {"id": "test-1", "name": "Updated Too"},
        ]

        updated_count = test_repository.bulk_update(updates)

        # Should only update 2 records (ones with ID)
        assert updated_count == 2

    def test_query_method(self, test_repository, sample_records):
        """Test getting base query for advanced filtering."""
        query = test_repository.query()

        # Should be able to use query for custom filtering
        result = query.filter(SampleModel.value > 20).all()
        assert len(result) == 2  # test-3 (30) and test-4 (40)

        # Can combine filters
        result = query.filter(
            SampleModel.value >= 20, SampleModel.name.like("Test%")
        ).all()
        assert len(result) == 3  # test-2, test-3, test-4

    def test_error_handling_create(self, test_repository, sample_records):
        """Test error handling in create method."""
        from sqlalchemy.exc import IntegrityError

        # Clear session to avoid instance conflicts
        test_repository.db.expunge_all()

        # Try to create duplicate ID
        duplicate_record = SampleModel(
            id="test-0",  # Already exists
            name="Duplicate",
            value=999,
        )

        with pytest.raises(IntegrityError):  # SQLAlchemy will raise IntegrityError
            test_repository.create(duplicate_record)

    def test_error_handling_update(self, test_repository, sample_records):
        """Test error handling in update method."""
        # Try to update with invalid data that would violate constraints
        # This depends on your actual model constraints
        # For this test model, we'll just verify the basic behavior

        # Update with empty dict should work but not change anything
        original_record = test_repository.get("test-0")
        updated_record = test_repository.update("test-0", {})

        assert updated_record is not None
        assert updated_record.name == original_record.name
        assert updated_record.value == original_record.value
