######## Frontend Build Stage ########
FROM node:24-alpine AS frontend-build
WORKDIR /app/frontend
RUN npm install -g pnpm
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ ./
RUN pnpm run build

######## Backend Production Stage ########
FROM python:3.12-slim-bookworm AS production
WORKDIR /app

# Install system dependencies and clean up in one layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Set optimization environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app
ENV STATIC_DIR=/app/static
ENV HOST=0.0.0.0
ENV PORT=8000
ENV WORKERS=1

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy built frontend and backend
COPY --from=frontend-build /app/frontend/dist ./static/
COPY backend/ ./

EXPOSE $PORT
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:$PORT/health || exit 1

CMD ["sh", "-c", "uvicorn main:app --host $HOST --port $PORT --workers $WORKERS"]
