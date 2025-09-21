#!/bin/bash
set -e

# Configuration
PROJECT_ID="beryl3"
REGION="europe-west4"
SERVICE_NAME="beryl3-qa-webapp"

echo "QA Webapp Status Report"
echo "======================"
echo ""

# Show service status
echo "Cloud Run Service:"
echo "------------------"
if gcloud run services describe $SERVICE_NAME --region=$REGION --project=$PROJECT_ID >/dev/null 2>&1; then
    gcloud run services describe $SERVICE_NAME \
      --region=$REGION \
      --project=$PROJECT_ID \
      --format="table(metadata.name,status.url,status.conditions[0].status,metadata.creationTimestamp)"
    
    echo ""
    echo "Service URL:"
    gcloud run services describe $SERVICE_NAME \
      --region=$REGION \
      --project=$PROJECT_ID \
      --format="value(status.url)"
    
    echo ""
    echo "Current Image:"
    gcloud run services describe $SERVICE_NAME \
      --region=$REGION \
      --project=$PROJECT_ID \
      --format="value(spec.template.spec.containers[0].image)"
else
    echo "Service '$SERVICE_NAME' not found."
fi

echo ""

# Show recent logs
echo "Recent Logs (last 10 entries):"
echo "------------------------------"
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" \
  --project=$PROJECT_ID \
  --limit=10 \
  --format="table(timestamp,severity,jsonPayload.message,textPayload)" 2>/dev/null || echo "No recent log entries found."

echo ""

# Show revisions
echo "Recent Revisions:"
echo "----------------"
gcloud run revisions list \
  --service=$SERVICE_NAME \
  --region=$REGION \
  --project=$PROJECT_ID \
  --limit=3 \
  --format="table(metadata.name,status.conditions[0].status,metadata.creationTimestamp)" 2>/dev/null || echo "No revisions found."

echo ""
echo "Commands:"
echo "---------"
echo "Deploy:     ./workflows/bin/deploy-qa-webapp.sh"
echo "Stop:       ./workflows/bin/stop-qa-webapp.sh"
echo "Remove:     ./workflows/bin/remove-qa-webapp.sh"
echo "View logs:  gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME\" --project=$PROJECT_ID --limit=20"