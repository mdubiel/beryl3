# Beryl3 Production Deployment Guide - Google Cloud Platform

## Overview

This guide provides step-by-step instructions for deploying Beryl3 to Google Cloud Platform using Docker containers. The application will be deployed using Cloud Run for the web application and Cloud SQL for the database.

## Prerequisites

- Google Cloud CLI installed and authenticated
- Docker installed locally
- Access to a Google Cloud project with billing enabled
- The application Docker image built and pushed to Google Artifact Registry

## Google Cloud Services Required

### 1. Enable Required APIs

```bash
gcloud services enable \
    run.googleapis.com \
    sql-component.googleapis.com \
    sqladmin.googleapis.com \
    storage-component.googleapis.com \
    artifactregistry.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com
```

### 2. Set Project Variables

```bash
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export SERVICE_NAME="beryl3-webapp"
export DB_INSTANCE_NAME="beryl3-db"
export BUCKET_NAME="beryl3-media-prod"
```

## Infrastructure Setup

### 1. Create Artifact Registry Repository

```bash
gcloud artifacts repositories create beryl3-repo \
    --repository-format=docker \
    --location=${REGION} \
    --description="Beryl3 application images"
```

### 2. Create Cloud SQL Instance (PostgreSQL)

```bash
# Create the PostgreSQL instance
gcloud sql instances create ${DB_INSTANCE_NAME} \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=${REGION} \
    --storage-type=SSD \
    --storage-size=20GB \
    --storage-auto-increase \
    --backup-start-time=03:00 \
    --enable-bin-log \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=04 \
    --deletion-protection

# Create the database
gcloud sql databases create beryl3_prod \
    --instance=${DB_INSTANCE_NAME}

# Create database user
gcloud sql users create beryl3_user \
    --instance=${DB_INSTANCE_NAME} \
    --password=GENERATE_SECURE_PASSWORD_HERE
```

### 3. Create Cloud Storage Bucket for Media Files

```bash
# Create the bucket
gsutil mb -p ${PROJECT_ID} -c STANDARD -l ${REGION} gs://${BUCKET_NAME}

# Set public read access for media files
gsutil iam ch allUsers:objectViewer gs://${BUCKET_NAME}

# Create folder structure
gsutil cp /dev/null gs://${BUCKET_NAME}/media/.keep
```

### 4. Create Service Account for Cloud Run

```bash
# Create service account
gcloud iam service-accounts create beryl3-service-account \
    --description="Service account for Beryl3 Cloud Run service" \
    --display-name="Beryl3 Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:beryl3-service-account@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:beryl3-service-account@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

# Create and download service account key
gcloud iam service-accounts keys create beryl3-service-key.json \
    --iam-account=beryl3-service-account@${PROJECT_ID}.iam.gserviceaccount.com
```

## Environment Variables Configuration

### Required Environment Variables for Cloud Run

Create these as Cloud Run environment variables or use Google Secret Manager:

#### Core Django Settings
```bash
SECRET_KEY="generate-secure-50-char-secret-key"
DEBUG=False
ALLOWED_HOSTS="your-cloudrun-service-url.run.app"
```

#### Database Configuration
```bash
DB_ENGINE="django.db.backends.postgresql"
PG_DB="beryl3_prod"
PG_USER="beryl3_user"
PG_PASSWORD="your-secure-database-password"
PG_HOST="/cloudsql/PROJECT_ID:REGION:DB_INSTANCE_NAME"  # Unix socket path
PG_PORT="5432"
```

#### Email Configuration (using Resend)
```bash
USE_INBUCKET=False
EMAIL_HOST="smtp.resend.com"
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER="resend"
EMAIL_HOST_PASSWORD="your-resend-api-key"
DEFAULT_FROM_EMAIL="Beryl3 <noreply@yourdomain.com>"
```

#### Google Cloud Storage
```bash
USE_GCS_STORAGE=True
GCS_BUCKET_NAME="beryl3-media-prod"
GCS_PROJECT_ID="your-project-id"
GCS_LOCATION="media"
# GCS_CREDENTIALS_PATH not needed - uses service account
```

#### Email Queue Configuration
```bash
POST_OFFICE_BATCH_SIZE=50
POST_OFFICE_BATCH_TIMEOUT=300
POST_OFFICE_MAX_RETRIES=3
POST_OFFICE_RETRY_INTERVAL=15
POST_OFFICE_MESSAGE_ID_FQDN="yourdomain.com"
```

#### Log Forwarding (Optional)
```bash
LOKI_ENABLED=False  # Disable for production - use Google Cloud Logging instead
```

#### External Service URLs (for Admin Panel)
```bash
EXTERNAL_DB_URL=""  # Leave empty for production
EXTERNAL_INBUCKET_URL=""  # Leave empty for production
EXTERNAL_MONITORING_URL="https://console.cloud.google.com/monitoring"
EXTERNAL_SENTRY_URL=""  # Configure when Sentry is re-enabled
```

#### Application Features
```bash
APPLICATION_ACTIVITY_LOGGING=True
SENTRY_ENVIRONMENT="production"
```

## Container Deployment

### 1. Build and Push Application Image

Assuming your Dockerfile is in the project root:

```bash
# Build the image
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/beryl3-repo/webapp:latest .

# Push to Artifact Registry
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/beryl3-repo/webapp:latest
```

### 2. Deploy to Cloud Run

```bash
# Deploy the service
gcloud run deploy ${SERVICE_NAME} \
    --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/beryl3-repo/webapp:latest \
    --platform=managed \
    --region=${REGION} \
    --service-account=beryl3-service-account@${PROJECT_ID}.iam.gserviceaccount.com \
    --add-cloudsql-instances=${PROJECT_ID}:${REGION}:${DB_INSTANCE_NAME} \
    --allow-unauthenticated \
    --memory=1Gi \
    --cpu=1 \
    --concurrency=100 \
    --max-instances=10 \
    --set-env-vars="DEBUG=False,USE_GCS_STORAGE=True" \
    # Add other environment variables as needed
```

### 3. Set Environment Variables (Alternative Method)

If you prefer to set environment variables after deployment:

```bash
# Set critical environment variables
gcloud run services update ${SERVICE_NAME} \
    --region=${REGION} \
    --set-env-vars="SECRET_KEY=your-secret-key,DEBUG=False,PG_HOST=/cloudsql/${PROJECT_ID}:${REGION}:${DB_INSTANCE_NAME}"
```

### 4. Run Database Migrations

```bash
# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format='value(status.url)')

# Run migrations (if you have a management command endpoint)
# Alternative: Use Cloud Build or run locally with Cloud SQL Proxy
```

## Log Collection Setup (Development/Staging)

For development and staging environments, you can deploy the log collection stack:

### 1. Deploy Log Collection to Cloud Run

```bash
# Deploy Loki
gcloud run deploy beryl3-loki \
    --image=grafana/loki:latest \
    --platform=managed \
    --region=${REGION} \
    --port=3100 \
    --memory=512Mi \
    --cpu=0.5 \
    --no-allow-unauthenticated

# Deploy Grafana
gcloud run deploy beryl3-grafana \
    --image=grafana/grafana:latest \
    --platform=managed \
    --region=${REGION} \
    --port=3000 \
    --memory=512Mi \
    --cpu=0.5 \
    --set-env-vars="GF_SECURITY_ADMIN_PASSWORD=secure-admin-password" \
    --no-allow-unauthenticated
```

### 2. Configure Log Forwarding

Update your webapp environment variables:
```bash
LOKI_ENABLED=True
LOKI_URL="https://beryl3-loki-xxx-uc.a.run.app"  # Use your Loki Cloud Run URL
```

## Domain Configuration

### 1. Map Custom Domain

```bash
# Map your domain to Cloud Run
gcloud run domain-mappings create \
    --service=${SERVICE_NAME} \
    --domain=yourdomain.com \
    --region=${REGION}
```

### 2. Update Environment Variables

```bash
# Update allowed hosts
gcloud run services update ${SERVICE_NAME} \
    --region=${REGION} \
    --set-env-vars="ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com"
```

## Security Configuration

### 1. Use Google Secret Manager (Recommended)

```bash
# Store secrets in Secret Manager
gcloud secrets create django-secret-key --data-file=-
# Enter your secret key when prompted

gcloud secrets create db-password --data-file=-
# Enter your database password when prompted

gcloud secrets create email-password --data-file=-
# Enter your email service password when prompted

# Grant Cloud Run service access to secrets
gcloud secrets add-iam-policy-binding django-secret-key \
    --member="serviceAccount:beryl3-service-account@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### 2. Update Cloud Run to Use Secrets

```yaml
# cloud-run-service.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: beryl3-webapp
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/cloudsql-instances: PROJECT_ID:REGION:DB_INSTANCE_NAME
    spec:
      serviceAccountName: beryl3-service-account@PROJECT_ID.iam.gserviceaccount.com
      containers:
      - image: REGION-docker.pkg.dev/PROJECT_ID/beryl3-repo/webapp:latest
        env:
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              key: latest
              name: django-secret-key
```

## Monitoring and Logging

### 1. Enable Google Cloud Logging

Logs are automatically collected by Google Cloud Logging. View them at:
```
https://console.cloud.google.com/logs/query?project=PROJECT_ID
```

### 2. Set Up Monitoring

```bash
# Create uptime check
gcloud alpha monitoring uptime create-http-check \
    --display-name="Beryl3 Uptime Check" \
    --hostname="yourdomain.com" \
    --path="/" \
    --port=443 \
    --use-ssl
```

## Backup Strategy

### 1. Automated Database Backups

Cloud SQL automatically creates daily backups. Configure additional settings:

```bash
gcloud sql instances patch ${DB_INSTANCE_NAME} \
    --backup-start-time=03:00 \
    --retained-backups-count=30 \
    --retained-transaction-log-days=7
```

### 2. Media Files Backup

Cloud Storage provides automatic redundancy, but consider:
- Cross-region replication for critical data
- Lifecycle policies for old files
- Regular backup testing

## Scaling Configuration

### 1. Cloud Run Scaling

```bash
# Update scaling settings
gcloud run services update ${SERVICE_NAME} \
    --region=${REGION} \
    --min-instances=1 \
    --max-instances=100 \
    --concurrency=80
```

### 2. Database Scaling

```bash
# Scale database if needed
gcloud sql instances patch ${DB_INSTANCE_NAME} \
    --tier=db-n1-standard-1 \
    --storage-size=100GB
```

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   - Verify Cloud SQL instance is running
   - Check service account permissions
   - Confirm unix socket path format

2. **File Upload Issues**
   - Verify GCS bucket permissions
   - Check service account has Storage Object Admin role
   - Confirm bucket name and project ID

3. **Email Issues**
   - Verify email service credentials
   - Check from address domain verification
   - Review email service quotas

### Logs and Debugging

```bash
# View Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=${SERVICE_NAME}" --limit=100

# View database logs
gcloud logging read "resource.type=cloudsql_database AND resource.labels.database_id=${PROJECT_ID}:${DB_INSTANCE_NAME}" --limit=50
```

## Cost Optimization

### 1. Resource Optimization
- Use appropriate Cloud Run CPU/memory settings
- Set minimum instances to 0 for development
- Use Cloud Storage lifecycle policies
- Monitor and adjust database tier

### 2. Budget Alerts
```bash
# Set up budget alerts
gcloud billing budgets create \
    --billing-account=YOUR_BILLING_ACCOUNT_ID \
    --display-name="Beryl3 Production Budget" \
    --budget-amount=100USD
```

## Deployment Checklist

- [ ] Enable required Google Cloud APIs
- [ ] Create Cloud SQL instance and database
- [ ] Create Cloud Storage bucket
- [ ] Set up service accounts and permissions
- [ ] Build and push Docker image
- [ ] Deploy to Cloud Run
- [ ] Configure environment variables
- [ ] Run database migrations
- [ ] Set up custom domain
- [ ] Configure monitoring and alerts
- [ ] Test all functionality
- [ ] Set up backup verification
- [ ] Document access credentials

## Maintenance

### Regular Tasks
- Monitor application performance and errors
- Review and rotate service account keys
- Update Docker images regularly
- Monitor costs and optimize resources
- Test backup and restore procedures
- Review security audit logs

### Updates and Deployments
```bash
# Deploy new version
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/beryl3-repo/webapp:v1.1.0 .
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/beryl3-repo/webapp:v1.1.0

gcloud run services update ${SERVICE_NAME} \
    --region=${REGION} \
    --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/beryl3-repo/webapp:v1.1.0
```

This deployment guide provides a comprehensive approach to deploying Beryl3 on Google Cloud Platform with proper security, monitoring, and scalability considerations.