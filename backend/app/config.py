"""
NarevAI Billing Analyzer - Application Configuration
"""

from functools import lru_cache
from typing import Any

from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = ConfigDict(
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    environment: str = Field(
        default="production", description="Application environment"
    )
    debug: bool = Field(default=False, description="Debug mode")

    # Database Selection
    database_type: str = Field(
        default="sqlite",
        description="Database type: currently only sqlite is supported",
    )

    # SQLite Configuration
    sqlite_path: str = Field(
        default="./data/billing.db", description="Path to SQLite database"
    )

    # PostgreSQL Configuration
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_db: str = Field(
        default="billing_analyzer", description="PostgreSQL database name"
    )
    postgres_user: str = Field(default="postgres", description="PostgreSQL user")
    postgres_password: str = Field(default="", description="PostgreSQL password")

    # Web Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")

    # DLT Configuration
    dlt_project_dir: str = Field(default=".dlt", description="DLT project directory")
    dlt_data_dir: str = Field(default=".dlt/data", description="DLT data directory")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_to_file: bool = Field(default=False, description="Log to file")
    log_file_path: str = Field(default="logs/app.log", description="Log file path")

    # API Configuration
    api_title: str = Field(default="NarevAI Billing Analyzer", description="API title")
    api_description: str = Field(
        default="FOCUS 1.2 compliant billing data analyzer for cloud and SaaS providers",
        description="API description",
    )
    api_version: str = Field(default="0.1.0", description="API version")

    # Demo mode
    demo: bool = Field(
        default=False,
        description="Demo mode - populate database with sample data on startup",
    )

    # Security
    encryption_key: str | None = Field(
        default=None, description="Fernet encryption key for API keys"
    )

    # CORS
    cors_origins: list[str] | str = Field(
        default=["http://localhost:8000", "http://localhost:3000"],
        description="CORS allowed origins",
    )

    focus_version: str = Field(default="1.2", description="FOCUS version")

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment setting."""
        if v not in ["development", "staging", "production"]:
            raise ValueError("Environment must be development, staging, or production")
        return v

    @field_validator("database_type")
    @classmethod
    def validate_database_type(cls, v):
        """Validate database type."""
        if v not in ["sqlite"]:
            raise ValueError(
                "Database type must be sqlite (postgres support coming soon)"
            )
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level setting."""
        if v.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError("Invalid log level")
        return v.upper()

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """Parse CORS origins from various formats."""
        if isinstance(v, str):
            if "," in v:
                return [origin.strip() for origin in v.split(",")]
            elif v.startswith("http"):
                return [v.strip()]
            elif v.startswith("["):
                import json

                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    return [v]
            else:
                return [v.strip()]
        elif isinstance(v, list):
            return v
        else:
            return ["http://localhost:8000", "http://localhost:3000"]

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, v: Any) -> bool:
        """Parse DEBUG environment variable to boolean."""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return bool(v)

    @field_validator("encryption_key")
    @classmethod
    def validate_encryption_key(cls, v, info):
        # Auto-generate encryption key in demo mode if not provided
        if not v and info.data.get("demo", False):
            from cryptography.fernet import Fernet

            generated_key = Fernet.generate_key().decode()
            print(f"🔑 Demo mode: Auto-generated encryption key: {generated_key}")
            return generated_key

        # Require encryption key in all environments (needed for API key encryption)
        if not v:
            raise ValueError(
                "Encryption key is required for encrypting sensitive data like API keys"
            )

        return v

    @property
    def database_url(self) -> str:
        """Get database URL based on configuration."""
        if self.database_type == "sqlite":
            return f"sqlite:///{self.sqlite_path}"
        elif self.database_type == "postgres":
            return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        else:
            raise ValueError(f"Unsupported database type: {self.database_type}")

    @property
    def demo_database_url(self) -> str:
        """Get demo database URL (separate from main database)."""
        if self.database_type == "sqlite":
            # Use demo.db for demo mode
            demo_path = self.sqlite_path.replace("billing.db", "demo.db")
            return f"sqlite:///{demo_path}"
        elif self.database_type == "postgres":
            # Use demo_ prefix for PostgreSQL database
            demo_db = f"demo_{self.postgres_db}"
            return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{demo_db}"
        else:
            raise ValueError(f"Unsupported database type: {self.database_type}")

    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite."""
        return self.database_type == "sqlite"

    @property
    def is_postgres(self) -> bool:
        """Check if using PostgreSQL."""
        return self.database_type == "postgres"

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"

    @property
    def database_config(self) -> dict[str, Any]:
        """Get database configuration for SQLAlchemy."""
        config = {
            "echo": self.debug and self.is_development,
            "pool_pre_ping": True,
        }

        if self.is_postgres:
            config.update(
                {
                    "pool_size": 20 if self.is_production else 5,
                    "max_overflow": 0 if self.is_production else 10,
                    "pool_recycle": 3600,
                }
            )

        return config

    @property
    def dlt_config(self) -> dict[str, Any]:
        """Get DLT configuration."""
        return {
            "project_dir": self.dlt_project_dir,
            "data_dir": self.dlt_data_dir,
            "destination": {
                "type": self.database_type,
                "credentials": self.database_url,
            },
        }

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as list (for compatibility)."""
        if isinstance(self.cors_origins, list):
            return self.cors_origins
        return [self.cors_origins]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
