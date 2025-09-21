# Unified Beryl3 Image - For both webapp and jobs
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/root/.local/bin:$PATH"

# Create app user and directories
RUN useradd --create-home --shell /bin/bash app && \
    mkdir -p /app/staticfiles /app/media /app/logs && \
    chown -R app:app /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Set working directory
WORKDIR /app

# Copy Python dependencies
COPY pyproject.toml ./

# Install Python dependencies
RUN uv sync

# Copy application code
COPY . .

# Create required directories
RUN mkdir -p logs static/css local_cdn

# Set permissions
RUN chmod +x /app/docker-entrypoint.sh

# Expose port
EXPOSE 8000

# Use unified entrypoint for both webapp and jobs
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default command for webapp
CMD ["webapp"]