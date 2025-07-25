"""
Database Configuration with SQLite and Auto-initialization
"""

import logging
import sqlite3
from pathlib import Path

from sqlalchemy import create_engine, orm
from sqlalchemy.orm import sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)

# Ensure data directory exists
Path("./data").mkdir(exist_ok=True)


def init_sqlite_if_needed():
    """Initialize SQLite database from migration if it doesn't exist."""
    if settings.database_type != "sqlite":
        return

    # Use demo database path if in demo mode
    if settings.demo:
        db_path = Path(settings.sqlite_path.replace("billing.db", "demo.db"))
        logger.info("Using demo database for demo mode")
    else:
        db_path = Path(settings.sqlite_path)

    if not db_path.exists():
        logger.info(f"Creating database from migration: {db_path}")

        # Ensure parent directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        with open("migrations/init_sqlite.sql") as f:
            cursor.executescript(f.read())

        conn.commit()
        conn.close()

        logger.info("Database created successfully")


# Initialize schema before creating engine
init_sqlite_if_needed()


# Create engine based on database type and demo mode
database_url = settings.demo_database_url if settings.demo else settings.database_url

if settings.database_type == "sqlite":
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
else:
    engine = create_engine(database_url, **settings.database_config)

# Create session factory
SessionLocal = sessionmaker(autoflush=False, bind=engine)

# Create base class for models
Base = orm.declarative_base()


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - SQLite uses migration, PostgreSQL uses SQLAlchemy."""

    if settings.database_type == "postgres":
        Base.metadata.create_all(bind=engine)

    logger.info(f"Database ready: {settings.database_type}")


def get_direct_connection():
    """Get direct database connection for analytics queries."""
    if settings.is_sqlite:
        import sqlite3

        # Use demo database if in demo mode
        if settings.demo:
            demo_path = settings.sqlite_path.replace("billing.db", "demo.db")
            return sqlite3.connect(demo_path)
        else:
            return sqlite3.connect(settings.sqlite_path)
    return None
