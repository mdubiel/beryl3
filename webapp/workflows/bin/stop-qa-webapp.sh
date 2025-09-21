#!/bin/bash
set -e

# Configuration
PROJECT_ID="beryl3"
REGION="europe-west4"
SERVICE_NAME="beryl3-qa-webapp"

echo "Stopping QA webapp service: $SERVICE_NAME"

# Scale to zero instances
gcloud run services update $SERVICE_NAME \
  --region=$REGION \
  --project=$PROJECT_ID \
  --min-instances=0 \
  --max-instances=0

echo "QA webapp service stopped (scaled to 0 instances)"
echo "Service status:"
gcloud run services describe $SERVICE_NAME \
  --region=$REGION \
  --project=$PROJECT_ID \
  --format="table(metadata.name,status.conditions[0].status)"