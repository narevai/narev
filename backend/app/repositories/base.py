"""
Base Repository Pattern
"""

import logging
from datetime import UTC, datetime
from typing import Any, TypeVar

from sqlalchemy import asc, desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Type variable for model
ModelType = TypeVar("ModelType", bound=DeclarativeMeta)


class BaseRepository[ModelType: DeclarativeMeta]:
    """Base repository with common CRUD operations."""

    def __init__(self, model: type[ModelType], db: Session):
        """
        Initialize repository.

        Args:
            model: SQLAlchemy model class
            db: Database session
        """
        self.model = model
        self.db = db

    def get(self, id: str) -> ModelType | None:
        """Get single record by ID."""
        try:
            return self.db.query(self.model).filter(self.model.id == id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model.__name__} by id {id}: {e}")
            return None

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: str | None = None,
        order_desc: bool = True,
    ) -> list[ModelType]:
        """Get all records with pagination."""
        try:
            query = self.db.query(self.model)

            # Apply ordering
            if order_by and hasattr(self.model, order_by):
                order_column = getattr(self.model, order_by)
                query = query.order_by(
                    desc(order_column) if order_desc else asc(order_column)
                )

            return query.offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting all {self.model.__name__}: {e}")
            return []

    def create(self, obj_in: ModelType) -> ModelType:
        """Create new record."""
        try:
            self.db.add(obj_in)
            self.db.commit()
            self.db.refresh(obj_in)
            return obj_in
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating {self.model.__name__}: {e}")
            raise

    def update(self, id: str, obj_in: dict[str, Any]) -> ModelType | None:
        """Update existing record."""
        try:
            db_obj = self.get(id)
            if not db_obj:
                return None

            # Update fields
            for field, value in obj_in.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)

            # Update timestamp if exists
            if hasattr(db_obj, "updated_at"):
                db_obj.updated_at = datetime.now(UTC)

            self.db.commit()
            self.db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating {self.model.__name__} {id}: {e}")
            raise

    def delete(self, id: str) -> bool:
        """Delete record by ID."""
        try:
            db_obj = self.get(id)
            if not db_obj:
                return False

            self.db.delete(db_obj)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting {self.model.__name__} {id}: {e}")
            return False

    def count(self, **filters) -> int:
        """Count records with optional filters."""
        try:
            query = self.db.query(self.model)

            # Apply filters
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)

            return query.count()
        except SQLAlchemyError as e:
            logger.error(f"Error counting {self.model.__name__}: {e}")
            return 0

    def exists(self, **filters) -> bool:
        """Check if record exists with given filters."""
        return self.count(**filters) > 0

    def bulk_create(self, objects: list[ModelType]) -> list[ModelType]:
        """Create multiple records in bulk."""
        try:
            self.db.add_all(objects)
            self.db.commit()

            # Refresh all objects
            for obj in objects:
                self.db.refresh(obj)

            return objects
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error bulk creating {self.model.__name__}: {e}")
            raise

    def bulk_update(self, updates: list[dict[str, Any]]) -> int:
        """
        Bulk update records.

        Args:
            updates: List of dicts with 'id' and fields to update

        Returns:
            Number of records updated
        """
        try:
            updated_count = 0

            for update_data in updates:
                if "id" not in update_data:
                    continue

                record_id = update_data.pop("id")
                result = self.update(record_id, update_data)
                if result:
                    updated_count += 1

            return updated_count
        except Exception as e:
            logger.error(f"Error bulk updating {self.model.__name__}: {e}")
            raise

    def query(self):
        """Get base query for advanced filtering."""
        return self.db.query(self.model)
