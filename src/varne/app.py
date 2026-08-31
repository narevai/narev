import sys

from fastapi import FastAPI
from loguru import logger
from nicegui import ui

from varne.api.v1 import router as v1_router
from varne.config import get_settings
from varne.ui.page import register_pages

settings = get_settings()

logger.remove()
logger.add(sys.stderr, level=settings.log_level)


def create_app() -> FastAPI:
    api = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.api_version,
        debug=settings.debug,
    )

    api.include_router(v1_router, prefix="/api/v1")
    register_pages()

    return api


app = create_app()
ui.run_with(app)
