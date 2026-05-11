# Use official Python runtime as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Make apt non-interactive and install only recommended packages to keep image small
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies including build tools for bcrypt
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
            ca-certificates \
            ffmpeg \
            curl \
            wget \
            gcc \
    # For video encoding/decoding
        g++ \
        make \
        libffi-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (better Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install Playwright browsers (Chromium) and dependencies for TikTok ingestion
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
# Refresh apt cache for install-deps to avoid stale indexes in slim images
RUN apt-get update && \
    playwright install-deps chromium && \
    playwright install chromium && \
    chown -R 1000:1000 /ms-playwright

# Create necessary directories with proper permissions
RUN mkdir -p uploads logs && \
    chmod 755 uploads logs

# Create non-root user for security (Cloud Run best practice)
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Cloud Run expects the app to listen on $PORT environment variable
# Default to 8080 if PORT is not set
ENV PORT=8080

# Expose port (documentation only, Cloud Run sets this automatically)
EXPOSE 8080

# Use exec form and environment variable for port
# This allows Cloud Run to set the port dynamically
# Use shell form so environment variables (like $PORT provided by Cloud Run)
# are properly expanded at container start time.
CMD exec gunicorn main:app --bind 0.0.0.0:${PORT} --worker-class uvicorn.workers.UvicornWorker --workers 1
