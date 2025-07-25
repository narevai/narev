"""
Logger configuration
"""

import logging
import os
import sys
import warnings
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging():
    """Configure logging for the application."""
    from app.config import get_settings

    settings = get_settings()

    # Start with console handler
    handlers = [logging.StreamHandler(sys.stdout)]

    # Add file handler if enabled
    if settings.log_to_file:
        file_handler = create_file_handler(settings.log_file_path)
        handlers.append(file_handler)

    # Configure root logger with all handlers
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s │ %(name)-30s │ %(levelname)-8s │ %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
        force=True,
    )

    # Configure third-party library logging
    configure_dependency_logging()

    # Make sure Python doesn't buffer
    os.environ["PYTHONUNBUFFERED"] = "1"

    # Log startup info
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {settings.log_level}")
    if settings.log_to_file:
        logger.info(f"File logging enabled - Path: {settings.log_file_path}")


def create_file_handler(log_file_path: str) -> RotatingFileHandler:
    """
    Create a rotating file handler for logging.

    Args:
        log_file_path: Path to the log file

    Returns:
        Configured RotatingFileHandler
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_file_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create rotating file handler (10MB per file, keep 5 backups)
    file_handler = RotatingFileHandler(
        filename=log_file_path,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )

    # Use same format as console
    file_handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s │ %(name)-30s │ %(levelname)-8s │ %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    return file_handler


def configure_dependency_logging():
    """
    Configure logging levels and filters for third-party dependencies.

    This function centralizes the configuration of external library logging
    to reduce noise and focus on application-specific logs. Add any new
    dependency log configurations here to keep them organized and documented.
    """

    # Azure SDK - Suppress verbose HTTP request/response logging
    # The Azure SDK logs every HTTP request and response at INFO level which
    # creates excessive noise in production logs
    logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(
        logging.WARNING
    )
    logging.getLogger("azure.storage.blob").setLevel(logging.WARNING)
    logging.getLogger("azure").setLevel(logging.WARNING)

    # SQLAlchemy/DLT - Suppress known warnings from merge operations
    # These warnings are about internal DLT implementation details that we cannot control:
    # - "Table already exists" occurs when DLT creates staging tables for merge operations
    # - "implicitly coercing SELECT" is about deprecated SQLAlchemy syntax in DLT's code
    # If SQLAlchemy is not installed, use regex filters
    warnings.filterwarnings("ignore", message="Table .* already exists")
    warnings.filterwarnings("ignore", message="implicitly coercing SELECT object")

    # DLT and pipeline specific loggers
    loggers_to_configure = [
        "pipeline.stages.extractors.bigquery",
        "providers.gcp.provider",
        "pipeline.stages.extract",
        "dlt",
        "google.cloud.bigquery",
    ]

    for logger_name in loggers_to_configure:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)

    # Add more dependency configurations as needed:
    # Example:
    # logging.getLogger("urllib3").setLevel(logging.WARNING)  # Reduce HTTP client verbosity
    # logging.getLogger("requests").setLevel(logging.WARNING)  # Reduce requests library logs
    # logging.getLogger("boto3").setLevel(logging.WARNING)     # AWS SDK
    # logging.getLogger("google").setLevel(logging.WARNING)     # Google Cloud SDK
