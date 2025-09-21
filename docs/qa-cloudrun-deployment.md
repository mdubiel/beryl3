# Beryl3 QA Cloud Run Deployment Guide

## Overview
This guide covers deploying and managing the Beryl3 Django application on Google Cloud Run for the QA environment with cost optimization.

## Prerequisites

### Required Tools
- Docker installed and running
- Google Cloud SDK (`gcloud`) installed and authenticated
- Ansible installed
- Make installed

### Required Permissions
Ensure your Google Cloud account has:
- `roles/run.admin` - Deploy and manage Cloud Run services
- `roles/artifactregistry.writer` - Push Docker images
- `roles/cloudsql.client` - Connect to Cloud SQL database
- `roles/storage.objectViewer` - Access GCS bucket
- `roles/logging.logWriter` - Write to Cloud Logging

## Cost-Optimized Configuration

### Resource Allocation
- **CPU**: 1 vCPU (minimum)
- **Memory**: 512Mi (sufficient for Django)
- **Scaling**: 0-2 instances (scale to zero for cost savings)
- **Concurrency**: 1000 requests per instance
- **CPU Allocation**: Only during request processing

### Estimated Costs (QA Environment)
- **Idle time**: $0 (scales to zero)
- **Active usage**: ~$0.10-0.50/day with moderate testing
- **Monthly cost**: $3-15 depending on usage

## Initial Deployment

### 1. Deploy to Cloud Run
```bash
cd /home/mdubiel/projects/beryl3/webapp
make qa-cloudrun-deploy
```

This command will:
1. Build the Docker image from current code
2. Push image to Google Artifact Registry
3. Deploy to Cloud Run with QA configuration
4. Configure public access
5. Display the service URL

### 2. Verify Deployment
```bash
# Check service status
make qa-cloudrun-info

# View recent logs
make qa-cloudrun-logs

# Test the application
curl [SERVICE_URL]
```

## Deploying New Versions

### Method 1: Version Tag Deployment (Recommended)
```bash
# First, update the version in VERSION file
make bump-build  # or bump-minor, bump-major

# Deploy with specific version tag
make qa-cloudrun-update TAG=v1.0.5
```

### Method 2: Latest Version Deployment
```bash
# Deploy latest code without version tag
make qa-cloudrun-deploy
```

### Method 3: Manual Version Control
```bash
# Build and tag image manually
make docker-build DOCKER_TAG=v1.0.5
make gcp-push DOCKER_TAG=v1.0.5

# Deploy specific tag
make qa-cloudrun-update TAG=v1.0.5
```

## Deployment Process Details

### What Happens During Deployment
1. **Code Preparation**: Current codebase is packaged
2. **Docker Build**: Image built with all dependencies
3. **Image Push**: Uploaded to Artifact Registry
4. **Service Update**: Cloud Run service updated with new image
5. **Health Checks**: Application startup verified
6. **Traffic Routing**: New version receives 100% traffic

### Zero-Downtime Deployment
Cloud Run automatically provides:
- **Blue-Green Deployment**: New revision runs alongside old
- **Health Checks**: Ensures new version is healthy before routing traffic
- **Automatic Rollback**: Returns to previous version if health checks fail

## Advanced Deployment Options

### Traffic Splitting (Canary Deployments)
```bash
# Deploy new version but don't route traffic yet
make qa-cloudrun-update TAG=v1.0.6

# Route 20% traffic to new version
make qa-cloudrun-traffic REVISION=beryl3-qa-webapp-xxx PERCENT=20

# If successful, route all traffic
make qa-cloudrun-traffic REVISION=beryl3-qa-webapp-xxx PERCENT=100
```

### Rollback to Previous Version
```bash
# Quick rollback to previous revision
make qa-cloudrun-rollback
```

### Scaling Management
```bash
# Temporarily scale to 2 instances (for load testing)
make qa-cloudrun-scale INSTANCES=2

# Return to cost-optimized scaling (0-2 auto)
make qa-cloudrun-scale INSTANCES=0
```

## Monitoring and Debugging

### View Logs
```bash
# Recent application logs
make qa-cloudrun-logs

# Live log streaming
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=beryl3-qa-webapp" --project=beryl3
```

### Check Service Health
```bash
# Service information and status
make qa-cloudrun-info

# Overall QA environment status
make qa-status
```

### Debug Deployment Issues
```bash
# View deployment events
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=beryl3-qa-webapp AND severity>=WARNING" --project=beryl3 --limit=20

# Check service configuration
gcloud run services describe beryl3-qa-webapp --region=europe-west6 --project=beryl3
```

## Environment Variables and Configuration

### Automatic Configuration
The deployment automatically configures:
- Database connection to Cloud SQL
- GCS storage integration
- Google Cloud Logging
- Sentry error tracking (if configured)
- Email service (Resend)

### Custom Configuration
To modify configuration:
1. Edit `ansible/inventories/qa.yml`
2. Update relevant variables
3. Redeploy: `make qa-cloudrun-deploy`

## Security Best Practices

### Service Account
- Uses dedicated `beryl3-qa-storage@beryl3.iam.gserviceaccount.com`
- Minimal required permissions only
- No service account keys stored in container

### Network Security
- HTTPS automatic termination
- IAM-based access control
- No VPC connector (cost optimization)

## Troubleshooting

### Common Issues

#### Deployment Fails
```bash
# Check if image build failed
docker images | grep beryl3-webapp

# Verify registry authentication
gcloud auth configure-docker europe-west6-docker.pkg.dev
```

#### Service Won't Start
```bash
# Check startup logs
make qa-cloudrun-logs

# Common issues:
# - Database connection (check credentials)
# - Missing environment variables
# - Static file collection errors
```

#### Database Connection Issues
```bash
# Verify Cloud SQL instance is running
gcloud sql instances describe beryl3-qa --project=beryl3

# Test connection from Cloud Shell
gcloud sql connect beryl3-qa --user=beryl3-qa --project=beryl3
```

### Cost Monitoring
```bash
# Monitor Cloud Run costs
gcloud billing budgets list --billing-account=[BILLING_ACCOUNT_ID]

# Check current usage
gcloud run services describe beryl3-qa-webapp --region=europe-west6 --project=beryl3 --format="value(status.observedGeneration)"
```

## Best Practices

### Development Workflow
1. **Local Testing**: Test changes locally first
2. **Version Tagging**: Always use semantic versioning
3. **Health Checks**: Verify deployment health before proceeding
4. **Monitoring**: Check logs after deployment

### Cost Optimization
1. **Scale to Zero**: Keep min instances at 0
2. **Resource Limits**: Don't over-allocate CPU/memory
3. **Regular Cleanup**: Remove old revisions periodically
4. **Monitor Usage**: Track costs and optimize accordingly

### Security
1. **Regular Updates**: Keep base images updated
2. **Secrets Management**: Use environment variables, not hardcoded values
3. **Access Control**: Limit who can deploy to QA
4. **Audit Logs**: Monitor deployment activities

## Quick Reference

### Essential Commands
```bash
# Deploy new version
make qa-cloudrun-update TAG=v1.0.5

# Check status
make qa-status

# View logs
make qa-cloudrun-logs

# Rollback
make qa-cloudrun-rollback

# Emergency stop (cost-saving)
make qa-cloudrun-scale INSTANCES=0
```

### Service URLs
- **Cloud Run Service**: Check `make qa-cloudrun-info` for current URL
- **Google Cloud Console**: https://console.cloud.google.com/run?project=beryl3
- **Artifact Registry**: https://console.cloud.google.com/artifacts?project=beryl3

For additional help, check the logs or contact the development team.