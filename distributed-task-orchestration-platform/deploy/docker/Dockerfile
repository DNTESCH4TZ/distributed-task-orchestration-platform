# Multi-stage Dockerfile for production deployment
# Optimized for size and security

# ========================================
# Stage 1: Base image with dependencies
# ========================================
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security (don't run as root)
RUN useradd -m -u 1000 -s /bin/bash appuser

WORKDIR /app

# ========================================
# Stage 2: Dependencies installation
# ========================================
FROM base as dependencies

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ========================================
# Stage 3: Final production image
# ========================================
FROM base as production

# Copy installed dependencies from previous stage
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser src /app/src
COPY --chown=appuser:appuser scripts /app/scripts
COPY --chown=appuser:appuser alembic.ini /app/

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"

# Run application with uvicorn
CMD ["uvicorn", "src.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--loop", "uvloop", \
     "--http", "httptools", \
     "--workers", "4", \
     "--backlog", "2048", \
     "--no-access-log"]

