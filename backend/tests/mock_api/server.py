"""
Mock OpenAI API Server for testing
"""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, Header, HTTPException, Response

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


app = FastAPI(title="Mock OpenAI API")

# Base directory for mock responses
RESPONSES_DIR = Path(__file__).parent / "responses" / "openai"


def load_json_file(filename: str) -> dict[str, Any]:
    """Load JSON file from responses directory."""
    filepath = RESPONSES_DIR / f"{filename}.json"
    logger.info(f"Loading file: {filepath}")

    if not filepath.exists():
        logger.error(f"File not found: {filepath}")
        raise HTTPException(status_code=500, detail=f"Mock file not found: {filename}")

    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    logger.info(f"Loaded {len(json.dumps(data))} bytes from {filename}")
    return data


def validate_auth(authorization: str | None = None):
    """Validate Bearer token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/v1/organization/usage/completions")
async def get_completions_usage(
    authorization: str = Header(None),
    start_time: int = None,
    end_time: int = None,
    bucket_width: str = "1d",
    group_by: str = None,
    limit: int = 30,
):
    """Mock completions usage endpoint."""
    validate_auth(authorization)

    logger.info(f"Completions request - start: {start_time}, end: {end_time}")

    data = load_json_file("completions_usage")
    return data


@app.get("/v1/organization/usage/embeddings")
async def get_embeddings_usage(
    authorization: str = Header(None),
    start_time: int = None,
    end_time: int = None,
    bucket_width: str = "1d",
    group_by: str = None,
    limit: int = 30,
):
    """Mock embeddings usage endpoint."""
    validate_auth(authorization)

    logger.info(f"Embeddings request - start: {start_time}, end: {end_time}")

    data = load_json_file("embeddings_usage")
    return data


@app.get("/v1/organization/usage/images")
async def get_images_usage(
    authorization: str = Header(None),
    start_time: int = None,
    end_time: int = None,
    bucket_width: str = "1d",
    group_by: str = None,
    limit: int = 30,
):
    """Mock images usage endpoint."""
    validate_auth(authorization)

    logger.info(f"Images request - start: {start_time}, end: {end_time}")

    data = load_json_file("images_usage")
    return data


@app.get("/v1/organization/usage/audio_speeches")
async def get_audio_speeches_usage(
    authorization: str = Header(None),
    start_time: int = None,
    end_time: int = None,
    bucket_width: str = "1d",
    group_by: str = None,
    limit: int = 30,
):
    """Mock audio speeches usage endpoint."""
    validate_auth(authorization)

    logger.info(f"Audio speeches request - start: {start_time}, end: {end_time}")

    data = load_json_file("audio_speeches_usage")
    return data


@app.get("/v1/organization/usage/audio_transcriptions")
async def get_audio_transcriptions_usage(
    authorization: str = Header(None),
    start_time: int = None,
    end_time: int = None,
    bucket_width: str = "1d",
    group_by: str = None,
    limit: int = 30,
):
    """Mock audio transcriptions usage endpoint."""
    validate_auth(authorization)

    logger.info(f"Audio transcriptions request - start: {start_time}, end: {end_time}")

    data = load_json_file("audio_transcriptions_usage")
    return data


@app.get("/v1/organization/usage/moderations")
async def get_moderations_usage(
    authorization: str = Header(None),
    start_time: int = None,
    end_time: int = None,
    bucket_width: str = "1d",
    group_by: str = None,
    limit: int = 30,
):
    """Mock moderations usage endpoint."""
    validate_auth(authorization)

    logger.info(f"Moderations request - start: {start_time}, end: {end_time}")

    data = load_json_file("moderations_usage")

    # Explicit JSON response to debug null issue
    json_str = json.dumps(data, ensure_ascii=False)
    return Response(
        content=json_str,
        media_type="application/json",
        headers={"Content-Type": "application/json; charset=utf-8"},
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.now(UTC).isoformat()}


if __name__ == "__main__":
    logger.info(f"Starting mock server with responses from: {RESPONSES_DIR}")

    # Verify responses directory exists
    if not RESPONSES_DIR.exists():
        logger.error(f"Responses directory not found: {RESPONSES_DIR}")
        logger.error("Create the directory and add mock JSON files")
        exit(1)

    # List available mock files
    json_files = list(RESPONSES_DIR.glob("*.json"))
    logger.info(f"Found {len(json_files)} mock response files:")
    for f in json_files:
        logger.info(f"  - {f.name}")

    uvicorn.run(app, host="0.0.0.0", port=8888, log_level="info")
