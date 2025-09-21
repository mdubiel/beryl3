#!/bin/bash
set -e

# Configuration
PROJECT_ID="beryl3"
REGION="europe-west4"

# Function to show available jobs
show_jobs() {
    echo "Available Cloud Run Jobs:"
    gcloud run jobs list --region=$REGION --project=$PROJECT_ID --format="table(metadata.name,status.conditions[0].type,status.conditions[0].status)" --filter="metadata.name~beryl3-qa-"
}

# Function to execute a job
execute_job() {
    local job_name=$1
    echo "Executing Cloud Run Job: $job_name"
    
    # Execute the job and capture the execution name
    local execution_output
    execution_output=$(gcloud run jobs execute $job_name --region=$REGION --project=$PROJECT_ID 2>&1)
    
    # Extract execution name from output
    local execution_name
    execution_name=$(echo "$execution_output" | grep -o "beryl3-qa-[a-z]*-[a-z0-9]*" | head -1)
    
    echo "Job execution started successfully!"
    echo "Execution name: $execution_name"
    echo ""
    echo "Monitor execution:"
    echo "   gcloud run jobs executions describe $execution_name --region=$REGION --project=$PROJECT_ID"
    echo ""
    echo "View logs:"
    echo "   gcloud logging read \"resource.type=cloud_run_job AND resource.labels.job_name=$job_name\" --project=$PROJECT_ID --limit=20"
    echo ""
    echo "Console URL:"
    echo "   https://console.cloud.google.com/run/jobs/executions/details/$REGION/$execution_name?project=$PROJECT_ID"
}

# Main logic
if [ $# -eq 0 ]; then
    echo "Cloud Run Job Execution Tool"
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

# Execute the job
execute_job $JOB_NAME