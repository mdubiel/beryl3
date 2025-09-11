# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create app user to avoid running as root
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy Python dependencies first (for better layer caching)
COPY pyproject.toml ./

# Install uv package manager
RUN pip install uv

# Install Python dependencies (let uv resolve dependencies)
RUN uv sync

# Copy package.json and install Node.js dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs static/css local_cdn

# Note: Using existing pre-built Tailwind CSS from static/css/tailwind.css
# If CSS needs to be rebuilt, run: make build-css on the host before building the image

# Static files are already built and included in the image
# collectstatic will be run during container startup if needed

# Change ownership of app directory to appuser
RUN chown -R appuser:appuser /app

# Create cache directory for uv with correct permissions
RUN mkdir -p /home/appuser/.cache/uv && chown -R appuser:appuser /home/appuser/.cache

# Switch to non-root user
USER appuser

# Copy entrypoint script
COPY --chown=appuser:appuser docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Use entrypoint script
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default command
CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]