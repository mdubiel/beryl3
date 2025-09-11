# Docker Deployment Guide

## Overview

This guide covers building, pushing, and deploying the Beryl3 Django application as a Docker container. The application is containerized for consistent deployment across different environments.

---

## Prerequisites

### Required Software
- **Docker Engine** (version 20.10 or later)
- **Make** (for simplified commands)
- **uv** (Python package manager)
- **Node.js & npm** (for Tailwind CSS)

### Registry Access
- **Staging Registry**: `192.168.1.14:5000`
- **Credentials**: `registry` / `registry123`
- **Web Interface**: http://registry.staging.mdubiel.org
- **Registry UI**: http://192.168.1.14:8082 (Visual interface)
- **Image Namespace**: `mdubiel.org`

---

## Quick Start

### Build and Push (Recommended)
```bash
# Navigate to webapp directory
cd webapp/

# Build and push to registry in one command
make docker-push
```

### Manual Steps
```bash
# 1. Build image locally
make docker-build

# 2. Push to staging registry
make docker-push

# 3. Get deployment information
make docker-deploy
```

---

## Detailed Build Process

### 1. Pre-build Requirements

**Tailwind CSS Build** (if styles changed):
```bash
cd webapp/
make build-css
```

**Environment Setup**:
- Ensure `.env` file exists for runtime configuration
- Static files should be pre-built (included in container)

### 2. Docker Image Build

**Using Make (Recommended)**:
```bash
cd webapp/
make docker-build
```

**Manual Docker Build**:
```bash
cd webapp/
docker build -t beryl3-webapp:latest .
```

**Build Process Details**:
- **Base Image**: `python:3.12-slim`
- **Size**: ~1.31GB (includes all dependencies)
- **User**: Non-root `appuser` for security
- **Dependencies**: Python (uv), Node.js (npm), system packages
- **Static Files**: Pre-built Tailwind CSS included

### 3. Registry Configuration

**Configure Docker for Insecure Registry** (one-time setup):
```bash
# Create Docker daemon configuration
sudo mkdir -p /etc/docker
echo '{"insecure-registries":["192.168.1.14:5000"]}' | sudo tee /etc/docker/daemon.json

# Restart Docker daemon
sudo systemctl restart docker
```

### 4. Push to Registry

**Using Make (Recommended)**:
```bash
cd webapp/
make docker-push
```

**Manual Registry Push**:
```bash
# Tag for registry with namespace
docker tag beryl3-webapp:latest 192.168.1.14:5000/mdubiel.org/beryl3-webapp:latest

# Login to registry
docker login 192.168.1.14:5000 -u registry -p registry123

# Push image
docker push 192.168.1.14:5000/mdubiel.org/beryl3-webapp:latest
```

---

## Make Commands Reference

### Available Targets

| Command | Description |
|---------|-------------|
| `make docker-build` | Build Docker image locally |
| `make docker-push` | Build and push to staging registry |
| `make docker-deploy` | Complete workflow with deployment info |
| `make help` | Show all available commands |

### Command Details

**`make docker-build`**:
- Builds image: `beryl3-webapp:latest`
- Includes all dependencies and static files
- Uses Docker cache for faster subsequent builds

**`make docker-push`**:
- Runs `docker-build` first
- Tags image for registry: `192.168.1.14:5000/mdubiel.org/beryl3-webapp:latest`
- Pushes to staging registry
- Shows final image location

**`make docker-deploy`**:
- Runs complete build and push workflow
- Displays deployment information
- Shows usage examples
- Provides Ansible integration details

---

## Container Configuration

### Dockerfile Features

**Multi-stage Optimizations**:
- System dependencies installed first (cached layer)
- Python dependencies with uv (faster installs)
- Node.js dependencies for Tailwind CSS
- Non-root user for security

**Runtime Configuration**:
- **Port**: 8000 (exposed)
- **Working Directory**: `/app`
- **User**: `appuser` (non-root)
- **Entrypoint**: `docker-entrypoint.sh`
- **Health Check**: HTTP check on port 8000

### Entrypoint Script (`docker-entrypoint.sh`)

**Startup Sequence**:
1. **Database Wait**: Waits for PostgreSQL availability
2. **Migrations**: Runs `python manage.py migrate`
3. **Static Files**: Runs `collectstatic` if needed
4. **Superuser**: Creates superuser from environment variables
5. **Application Start**: Launches Django development server

**Environment Variables**:
```bash
# Database configuration (required)
DATABASE_URL=postgres://user:pass@host:5432/dbname
# OR individual variables:
PG_HOST=localhost
PG_PORT=5432
PG_DB=beryl3
PG_USER=beryl3_user
PG_PASSWORD=secure_password

# Django configuration (required)
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com,localhost

# Optional superuser creation
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=admin_password
```

---

## Deployment

### Local Testing
```bash
# Run container locally
docker run -d \
  --name beryl3-webapp \
  -p 8000:8000 \
  --env-file .env \
  192.168.1.14:5000/mdubiel.org/beryl3-webapp:latest

# Check logs
docker logs beryl3-webapp

# Test application
curl http://localhost:8000/
```

### Production Deployment

**Docker Compose Example**:
```yaml
version: '3.8'
services:
  webapp:
    image: 192.168.1.14:5000/mdubiel.org/beryl3-webapp:latest
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
    restart: unless-stopped
    
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: beryl3
      POSTGRES_USER: beryl3_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

**Ansible Integration**:
```yaml
# In your Ansible playbook
- name: Deploy Beryl3 application
  docker_container:
    name: beryl3-webapp
    image: "192.168.1.14:5000/mdubiel.org/beryl3-webapp:latest"
    ports:
      - "8000:8000"
    env_file: "{{ app_root }}/.env"
    restart_policy: unless-stopped
    pull: true
```

---

## Troubleshooting

### Build Issues

**Missing Dependencies**:
```bash
# Install required tools
sudo apt-get update
sudo apt-get install docker.io make curl

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Build Cache Issues**:
```bash
# Clear Docker build cache
docker builder prune

# Force rebuild without cache
docker build --no-cache -t beryl3-webapp:latest .
```

### Registry Issues

**Connection Refused**:
```bash
# Verify registry is running
curl http://192.168.1.14:5000/v2/_catalog

# Check insecure registry configuration
cat /etc/docker/daemon.json
```

**Authentication Failed**:
```bash
# Re-login to registry
docker logout 192.168.1.14:5000
docker login 192.168.1.14:5000 -u registry -p registry123
```

### Runtime Issues

**Database Connection**:
```bash
# Check database connectivity
docker run --rm -it \
  --env-file .env \
  192.168.1.14:5000/mdubiel.org/beryl3-webapp:latest \
  uv run python manage.py check --database default
```

**Static Files Missing**:
```bash
# Rebuild CSS locally first
make build-css

# Then rebuild container
make docker-build
```

**Permission Issues**:
```bash
# Check container logs
docker logs beryl3-webapp

# Run as different user (debugging only)
docker run --user root -it 192.168.1.14:5000/mdubiel.org/beryl3-webapp:latest bash
```

---

## Registry Management

### View Available Images

**API Access**:
```bash
# List all repositories
curl -u registry:registry123 http://192.168.1.14:5000/v2/_catalog

# Get image tags (with namespace)
curl -u registry:registry123 http://192.168.1.14:5000/v2/mdubiel.org/beryl3-webapp/tags/list

# Get image manifest
curl -u registry:registry123 http://192.168.1.14:5000/v2/mdubiel.org/beryl3-webapp/manifests/latest
```

**Web Interface**:
- **Registry UI**: http://192.168.1.14:8082 (Full visual interface)
- **Basic API**: http://registry.staging.mdubiel.org
- **Username**: `registry`
- **Password**: `registry123`

**Features of Registry UI (v2.0)**:
- Browse repositories and tags visually
- View image details and layers
- Delete images (if enabled)
- Search functionality
- Content digest display
- Enhanced catalog browsing (up to 1000 elements)
- Improved performance and modern interface

### Image Cleanup
```bash
# Remove local images
docker rmi beryl3-webapp:latest
docker rmi 192.168.1.14:5000/mdubiel.org/beryl3-webapp:latest

# Prune unused images
docker image prune
```

---

## Security Considerations

### Container Security
- **Non-root User**: Runs as `appuser` (UID/GID managed by Docker)
- **Minimal Base**: Uses `python:3.12-slim` (reduced attack surface)
- **No Secrets**: Secrets loaded from environment at runtime
- **Health Checks**: Built-in application health monitoring

### Registry Security
- **HTTP Only**: Currently uses HTTP (staging environment)
- **Basic Auth**: Username/password authentication
- **Internal Network**: Registry accessible only within staging network
- **Future**: Plan for HTTPS with Let's Encrypt certificates

### Production Recommendations
- Use HTTPS registry with proper certificates
- Implement image scanning for vulnerabilities
- Use secrets management system (not environment variables)
- Regular security updates for base images

---

## Performance Optimization

### Build Performance
```bash
# Use BuildKit for faster builds
export DOCKER_BUILDKIT=1
docker build -t beryl3-webapp:latest .

# Multi-stage builds (already implemented)
# Dependency caching (already implemented)
```

### Runtime Performance
```bash
# Use production WSGI server instead of development server
# Update Dockerfile CMD to use gunicorn:
CMD ["uv", "run", "gunicorn", "--bind", "0.0.0.0:8000", "webapp.wsgi:application"]
```

### Image Size Optimization
- Current size: ~1.31GB
- Optimization opportunities:
  - Multi-stage builds to exclude build tools
  - Alpine Linux base images
  - Remove development dependencies in production

---

## Integration with CI/CD

### GitHub Actions Example
```yaml
name: Build and Deploy
on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Build and push Docker image
      run: |
        cd webapp
        make docker-push
        
    - name: Deploy to staging
      run: |
        # Your deployment commands here
        echo "Deployed: 192.168.1.14:5000/mdubiel.org/beryl3-webapp:latest"
```

---

## Monitoring and Logging

### Container Logs
```bash
# View real-time logs
docker logs -f beryl3-webapp

# Get last 100 lines
docker logs --tail 100 beryl3-webapp

# Logs since specific time
docker logs --since 2h beryl3-webapp
```

### Application Logs
- **Django Logs**: `/app/logs/django.log`
- **Performance Logs**: `/app/logs/performance.jsonl`
- **Application Logs**: `/app/logs/webapp.jsonl`

### Health Monitoring
```bash
# Check container health
docker ps
# Look for "healthy" status

# Manual health check
curl http://localhost:8000/
```

---

## Next Steps

1. **Production Readiness**:
   - Implement HTTPS registry
   - Add vulnerability scanning
   - Use production WSGI server

2. **Automation**:
   - CI/CD pipeline integration
   - Automated testing in containers
   - Staging deployment automation

3. **Monitoring**:
   - Container metrics collection
   - Log aggregation setup
   - Application performance monitoring

---

*For additional help, refer to the main [documentation index](index.md) or check the [infrastructure services](infrastructure-services.md) documentation.*