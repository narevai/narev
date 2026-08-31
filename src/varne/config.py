from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000

    log_level: str = "INFO"

    api_title: str = "Varne"
    api_description: str = "Varne API"
    api_version: str = "1.0.0-alpha.0"

    database_path: str = "./data/app.duckdb"


@lru_cache
def get_settings() -> Settings:
    return Settings()
