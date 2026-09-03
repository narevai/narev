from functools import lru_cache

import httpx2 as httpx
import ibis

from varne.config import get_settings
from varne.db.connection import create_connection
from varne.db.schema import create_tables
from varne.http import create_http_client
from varne.providers.base import ProviderService
from varne.providers.jsonplaceholder.client import JsonPlaceholderClient
from varne.providers.jsonplaceholder.service import JsonPlaceholderService


@lru_cache
def get_db() -> ibis.BaseBackend:
    settings = get_settings()

    db = create_connection(settings.database_path)
    create_tables(db)

    return db


@lru_cache
def get_http() -> httpx.Client:
    return create_http_client()


def get_json_placeholder_service() -> ProviderService:
    return JsonPlaceholderService(
        db=get_db(), client=JsonPlaceholderClient(http=get_http())
    )
