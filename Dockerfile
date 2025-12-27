# Multi-stage Dockerfile for Teams Agent Integration Services
# Supports both receiver (port 3001) and notifier (port 8001) services

FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements/base.txt requirements/
RUN pip install --no-cache-dir -r requirements/base.txt

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Default environment
ENV ENVIRONMENT=production \
    LOG_LEVEL=INFO

# -----------------------------------------------------------
# Receiver Service (Teams Webhook -> Agent)
# -----------------------------------------------------------
FROM base AS receiver

ENV SERVICE_NAME=receiver \
    RECEIVER_PORT=3001

EXPOSE 3001

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3001/health || exit 1

CMD ["python", "-m", "uvicorn", "src.api.receiver_api:app", "--host", "0.0.0.0", "--port", "3001"]

# -----------------------------------------------------------
# Notifier Service (Agent -> Teams)
# -----------------------------------------------------------
FROM base AS notifier

ENV SERVICE_NAME=notifier \
    NOTIFIER_PORT=8001

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

CMD ["python", "-m", "uvicorn", "src.api.notifier_api:app", "--host", "0.0.0.0", "--port", "8001"]
