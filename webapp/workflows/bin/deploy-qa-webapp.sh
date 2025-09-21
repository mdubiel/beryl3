#!/bin/bash
set -e

# Configuration
PROJECT_ID="beryl3"
REGION="europe-west4"
SERVICE_NAME="beryl3-qa-webapp"
IMAGE="europe-west6-docker.pkg.dev/beryl3/beryl3/beryl3-webapp:latest"

echo "Deploying QA webapp service: $SERVICE_NAME"
echo "Using image: $IMAGE"

gcloud run services replace cloudrun-qa.yaml \
  --region=$REGION \
  --project=$PROJECT_ID

echo "QA webapp deployed successfully!"
echo "Service URL:"
gcloud run services describe $SERVICE_NAME \
  --region=$REGION \
  --project=$PROJECT_ID \
  --format="value(status.url)"