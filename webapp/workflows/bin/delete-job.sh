#!/bin/bash
set -e

# Configuration
PROJECT_ID="beryl3"
REGION="europe-west4"

# Function to show available jobs
show_jobs() {
    echo "Available Cloud Run Jobs:"
    gcloud run jobs list --region=$REGION --project=$PROJECT_ID --format="table(metadata.name,metadata.labels.environment)" --filter="metadata.name~beryl3-qa-"
}

# Function to delete a job
delete_job() {
    local job_name=$1
    echo "Deleting Cloud Run Job: $job_name"
    gcloud run jobs delete $job_name --region=$REGION --project=$PROJECT_ID --quiet
    echo "Job $job_name deleted successfully!"
}

# Main logic
if [ $# -eq 0 ]; then
    echo "Cloud Run Job Deletion Tool"
    echo ""
    show_jobs
    echo ""
    echo "Usage: $0 <job-name>"
    echo "Example: $0 beryl3-qa-collectstatic"
    echo ""
    echo "Available job names:"
    gcloud run jobs list --region=$REGION --project=$PROJECT_ID --format="value(metadata.name)" --filter="metadata.name~beryl3-qa-" | sed 's/^/  - /'
    exit 1
fi

JOB_NAME=$1

# Check if job exists
if ! gcloud run jobs describe $JOB_NAME --region=$REGION --project=$PROJECT_ID >/dev/null 2>&1; then
    echo "Job '$JOB_NAME' not found!"
    echo ""
    show_jobs
    exit 1
fi

# Confirm deletion
echo "WARNING: Are you sure you want to delete job '$JOB_NAME'? [y/N]"
read -r confirmation
if [[ $confirmation =~ ^[Yy]$ ]]; then
    delete_job $JOB_NAME
else
    echo "Deletion cancelled."
    exit 1
fi