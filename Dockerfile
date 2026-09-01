FROM python:3.14-slim-bookworm AS production
WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000

COPY pyproject.toml uv.lock ./
COPY src/ ./src/
RUN pip install --no-cache-dir --upgrade pip uv && \
    uv export --frozen --no-dev --no-hashes --no-emit-project | uv pip install --system -r - && \
    uv pip install --system --no-deps -e .

EXPOSE $PORT
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:$PORT/api/v1/health || exit 1

CMD ["python", "-m", "varne.app"]
