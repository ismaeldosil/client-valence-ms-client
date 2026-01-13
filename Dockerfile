# Dockerfile for Valerie MS Teams Client
# Single service that runs webhook receiver + dashboard

FROM python:3.12-slim

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
COPY requirements/base.txt requirements/base.txt
RUN pip install --no-cache-dir -r requirements/base.txt

# Copy application code
COPY src/ src/
COPY scripts/ scripts/
COPY docs/ docs/

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Default environment
ENV ENVIRONMENT=production \
    LOG_LEVEL=INFO

# The PORT will be injected by Railway
# CMD uses python -m to run the main module
CMD ["python", "-m", "src.main"]
