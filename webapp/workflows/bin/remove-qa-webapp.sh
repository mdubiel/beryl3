#!/bin/bash
set -e

# Configuration
PROJECT_ID="beryl3"
REGION="europe-west4"
SERVICE_NAME="beryl3-qa-webapp"

echo "Removing QA webapp service: $SERVICE_NAME"

# Confirm deletion
echo "WARNING: Are you sure you want to delete the QA webapp service? [y/N]"
read -r confirmation
if [[ ! $confirmation =~ ^[Yy]$ ]]; then
    echo "Deletion cancelled."
    exit 1
fi

gcloud run services delete $SERVICE_NAME \
  --region=$REGION \
  --project=$PROJECT_ID \
  --quiet

echo "QA webapp service deleted successfully!"

# Verify removal
echo "Remaining Cloud Run services:"
gcloud run services list --region=$REGION --project=$PROJECT_ID --filter="metadata.name~beryl3-qa-" || echo "No beryl3-qa-* services remaining."