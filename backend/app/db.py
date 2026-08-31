import ibis
from loguru import logger

from app.config import get_settings

_connection: ibis.BaseBackend | None = None


def get_connection() -> ibis.BaseBackend:
    global _connection
    if _connection is None:
        settings = get_settings()
        logger.debug("Connecting to DuckDB at {}", settings.database_path)
        _connection = ibis.duckdb.connect(settings.database_path)
    return _connection
