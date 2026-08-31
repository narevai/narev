FROM python:3.12-slim-bookworm AS production
WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app
ENV HOST=0.0.0.0
ENV PORT=8000
ENV WORKERS=1

COPY backend/pyproject.toml backend/uv.lock ./
RUN pip install --no-cache-dir --upgrade pip uv && \
    uv export --frozen --no-dev --no-emit-project --no-hashes | uv pip install --system -r -

COPY backend/ ./

EXPOSE $PORT
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:$PORT/api/v1/health || exit 1

CMD ["sh", "-c", "uvicorn main:app --host $HOST --port $PORT --workers $WORKERS"]
