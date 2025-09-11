# Beryl3 Staging Environment

Production-like staging deployment for **beryl3-stage.mdubiel.org** with nginx frontend, internal Docker networking, and external log monitoring access.

## Architecture Overview

```
Internet → nginx (ports 80/443) → Django App + Internal Network
                ↓ (port 3000)
              Grafana (log monitoring)

Internal Network (172.20.0.0/16):
├── nginx (172.20.0.30) - Frontend proxy
├── webapp (172.20.0.20) - Django application  
├── postgres (172.20.0.10) - Database
├── redis (172.20.0.11) - Cache/sessions
├── loki (172.20.0.40) - Log collection
└── grafana (172.20.0.41) - Log visualization
```

## Prerequisites

### 1. Domain Setup
- Ensure DNS A record for `beryl3-stage.mdubiel.org` points to your server IP
- SSL certificate files ready (see SSL Configuration below)

### 2. GCS Configuration
- Google Cloud Storage bucket created
- Service account key JSON file downloaded
- Bucket permissions configured for public read access

### 3. Email Service
- Resend API key obtained
- Domain verification completed in Resend

## Quick Start

### 1. Environment Setup

```bash
cd /home/mdubiel/projects/beryl3/staging

# Copy and customize environment file
cp .env.staging .env
nano .env  # Edit with your actual values
```

**Required .env changes:**
```bash
# Update these with your actual values:
WEBAPP_IMAGE_URL=us-central1-docker.pkg.dev/your-project-id/beryl3-repo/webapp:latest
GCS_BUCKET_NAME=your_actual_bucket_name
GCS_PROJECT_ID=your_gcp_project_id
GCS_CREDENTIALS_PATH=/path/to/your/service-account-key.json
EMAIL_HOST_PASSWORD=your_resend_api_key
SECRET_KEY=generate_50_char_random_string
PG_PASSWORD=create_secure_database_password
REDIS_PASSWORD=create_secure_redis_password
GRAFANA_ADMIN_PASSWORD=create_secure_grafana_password
```

### 2. SSL Certificate Setup

```bash
# Create SSL directory
mkdir -p ssl

# Option A: Let's Encrypt (recommended)
sudo certbot certonly --standalone -d beryl3-stage.mdubiel.org
sudo cp /etc/letsencrypt/live/beryl3-stage.mdubiel.org/fullchain.pem ssl/beryl3-stage.mdubiel.org.crt
sudo cp /etc/letsencrypt/live/beryl3-stage.mdubiel.org/privkey.pem ssl/beryl3-stage.mdubiel.org.key

# Option B: Self-signed (development only)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/beryl3-stage.mdubiel.org.key \
  -out ssl/beryl3-stage.mdubiel.org.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=beryl3-stage.mdubiel.org"
```

### 3. Deploy Services

```bash
# Pull the latest application image
docker pull $WEBAPP_IMAGE_URL

# Start all services
docker-compose -f docker-compose.staging.yaml --env-file .env up -d

# Verify services are running
docker-compose -f docker-compose.staging.yaml ps
```

### 4. Database Setup

```bash
# Run migrations
docker-compose -f docker-compose.staging.yaml exec webapp python manage.py migrate

# Create superuser
docker-compose -f docker-compose.staging.yaml exec webapp python manage.py createsuperuser

# Collect static files (if not using GCS for static)
docker-compose -f docker-compose.staging.yaml exec webapp python manage.py collectstatic --noinput
```

## Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| **Main Application** | https://beryl3-stage.mdubiel.org | Primary web interface |
| **Admin Panel** | https://beryl3-stage.mdubiel.org/admin/ | Django admin |
| **SYS Panel** | https://beryl3-stage.mdubiel.org/sys/ | System management |
| **Grafana (via nginx)** | https://beryl3-stage.mdubiel.org/grafana/ | Log monitoring (subpath) |
| **Grafana (direct)** | http://your-server-ip:3000 | Direct access for admin |

## Service Management

### Start/Stop Services
```bash
# Start all services
docker-compose -f docker-compose.staging.yaml --env-file .env up -d

# Stop all services
docker-compose -f docker-compose.staging.yaml down

# Restart specific service
docker-compose -f docker-compose.staging.yaml restart webapp

# View logs
docker-compose -f docker-compose.staging.yaml logs -f webapp
```

### Application Updates
```bash
# Pull new image
docker pull $WEBAPP_IMAGE_URL

# Update and restart webapp
docker-compose -f docker-compose.staging.yaml up -d webapp

# Run migrations if needed
docker-compose -f docker-compose.staging.yaml exec webapp python manage.py migrate
```

### Database Management
```bash
# Backup database
docker-compose -f docker-compose.staging.yaml exec postgres pg_dump -U beryl3_staging beryl3_staging > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore database
cat backup_file.sql | docker-compose -f docker-compose.staging.yaml exec -T postgres psql -U beryl3_staging -d beryl3_staging

# Database shell
docker-compose -f docker-compose.staging.yaml exec postgres psql -U beryl3_staging -d beryl3_staging
```

## Configuration Details

### Network Architecture
- **Custom bridge network:** `172.20.0.0/16`
- **Internal communication:** Services use container names (postgres, redis, loki, grafana)
- **External access:** Only nginx (ports 80/443/3000) exposed
- **Security:** All internal services isolated from external access

### Storage
- **Static files:** Google Cloud Storage (configured via GCS_* env vars)
- **Media files:** Google Cloud Storage (user uploads)
- **Database:** PostgreSQL with persistent volume
- **Logs:** Loki with 14-day retention
- **Redis:** Persistent storage for sessions/cache

### Email
- **Service:** Resend SMTP
- **Queue:** Django Post Office with dedicated worker process
- **Templates:** HTML + plain text fallbacks
- **Delivery:** Asynchronous with retry logic

### Monitoring
- **Application logs:** Forward to Loki → view in Grafana
- **System logs:** Docker container logs
- **Health checks:** All services have health check endpoints
- **Access logs:** Nginx access and error logs

## Security Features

### SSL/TLS
- **Automatic HTTPS redirect** from port 80
- **Modern TLS configuration** (TLS 1.2/1.3 only)
- **Security headers:** HSTS, XSS protection, frame denial
- **Let's Encrypt ready** with ACME challenge support

### Network Security
- **Internal network isolation**
- **Service-to-service communication** via container names
- **Rate limiting** on web requests
- **Nginx proxy** hides internal service details

### Application Security
- **Production Django settings:** DEBUG=False, security headers
- **Secure cookies:** HTTPS-only session and CSRF cookies  
- **Secret management:** Environment variables for all secrets
- **Database isolation:** Dedicated user with limited permissions

## Monitoring and Logs

### Log Collection
- **Django logs → Loki:** All application logs forwarded
- **Grafana interface:** Real-time log viewing and searching
- **Log retention:** 14 days in staging environment
- **External access:** Grafana available on port 3000 and /grafana/ subpath

### Health Monitoring
```bash
# Check service health
docker-compose -f docker-compose.staging.yaml exec webapp python manage.py check --deploy

# View service status
docker-compose -f docker-compose.staging.yaml ps

# Monitor logs in real-time
docker-compose -f docker-compose.staging.yaml logs -f
```

## Troubleshooting

### Common Issues

**1. SSL Certificate Issues**
```bash
# Check certificate validity
openssl x509 -in ssl/beryl3-stage.mdubiel.org.crt -text -noout

# Verify nginx config
docker-compose -f docker-compose.staging.yaml exec nginx nginx -t
```

**2. Database Connection Issues**
```bash
# Test database connection
docker-compose -f docker-compose.staging.yaml exec webapp python manage.py dbshell

# Check database logs
docker-compose -f docker-compose.staging.yaml logs postgres
```

**3. GCS Storage Issues**
```bash
# Test GCS authentication
docker-compose -f docker-compose.staging.yaml exec webapp python -c "
from google.cloud import storage
client = storage.Client()
bucket = client.bucket('$GCS_BUCKET_NAME')
print(f'Bucket exists: {bucket.exists()}')
"
```

**4. Email Issues**
```bash
# Test email configuration
docker-compose -f docker-compose.staging.yaml exec webapp python manage.py shell -c "
from django.core.mail import send_mail
result = send_mail('Test', 'Test message', 'staging@mdubiel.org', ['test@example.com'])
print(f'Email sent: {result}')
"

# Check email queue
docker-compose -f docker-compose.staging.yaml logs email_worker
```

### Log Analysis
- **Grafana:** https://beryl3-stage.mdubiel.org/grafana/
- **Direct Grafana:** http://your-server-ip:3000
- **Container logs:** `docker-compose logs [service_name]`

## Maintenance

### Regular Tasks
- **Monitor disk usage:** Docker volumes can grow large
- **Rotate logs:** Configure log rotation for nginx
- **Update images:** Regularly pull latest application images
- **Backup database:** Automated daily backups recommended
- **Monitor SSL:** Certificate renewal (Let's Encrypt auto-renewal)

### Updates and Deployments
```bash
# Deploy new application version
export NEW_IMAGE="us-central1-docker.pkg.dev/project/beryl3-repo/webapp:v1.2.0"
sed -i "s|WEBAPP_IMAGE_URL=.*|WEBAPP_IMAGE_URL=$NEW_IMAGE|" .env
docker-compose -f docker-compose.staging.yaml up -d webapp
```

This staging environment provides a production-like setup for testing and validation before deploying to Google Cloud Platform.