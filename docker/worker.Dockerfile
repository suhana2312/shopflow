# Worker Dockerfile for Celery background tasks & DLQ processing
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend application source
COPY backend/ .

# Default command runs the Celery worker
CMD ["celery", "-A", "app.workers.celery_app.celery", "worker", "--loglevel=INFO", "-Q", "orders_queue,dlq,celery", "--concurrency=4"]
