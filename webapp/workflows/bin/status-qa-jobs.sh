#!/bin/bash
set -e

# Configuration
PROJECT_ID="beryl3"
REGION="europe-west4"

echo "QA Jobs Status Report"
echo "===================="
echo ""

# Show all beryl3-qa-* jobs with their status
echo "Cloud Run Jobs:"
echo "---------------"
gcloud run jobs list --region=$REGION --project=$PROJECT_ID --format="table(metadata.name,status.conditions[0].type,status.conditions[0].status,metadata.creationTimestamp)" --filter="metadata.name~beryl3-qa-" || echo "No beryl3-qa-* jobs found."

echo ""

# Show recent executions for each job
echo "Recent Job Executions:"
echo "---------------------"

JOBS=$(gcloud run jobs list --region=$REGION --project=$PROJECT_ID --format="value(metadata.name)" --filter="metadata.name~beryl3-qa-" 2>/dev/null)

if [ -z "$JOBS" ]; then
    echo "No beryl3-qa-* jobs found."
else
    while IFS= read -r job; do
        if [ -n "$job" ]; then
            echo ""
            echo "Job: $job"
            echo "$(printf '%.0s-' {1..40})"
            
            # Get recent executions for this job
            EXECUTIONS=$(gcloud run jobs executions list --region=$REGION --project=$PROJECT_ID --job=$job --limit=3 --format="table(metadata.name,status.conditions[0].type,status.conditions[0].status,metadata.creationTimestamp)" 2>/dev/null)
            
            if [ -n "$EXECUTIONS" ]; then
                echo "$EXECUTIONS"
            else
                echo "No executions found for $job"
            fi
        fi
    done <<< "$JOBS"
fi

echo ""

# Show recent logs from all QA jobs
echo "Recent Log Activity (last 10 entries):"
echo "--------------------------------------"
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name~beryl3-qa-" --project=$PROJECT_ID --limit=10 --format="table(timestamp,resource.labels.job_name,severity,jsonPayload.message,textPayload)" 2>/dev/null || echo "No recent log entries found."

echo ""

# Show summary
echo "Summary:"
echo "--------"
JOB_COUNT=$(echo "$JOBS" | grep -c . 2>/dev/null || echo "0")
echo "Total beryl3-qa-* jobs: $JOB_COUNT"

# Count running executions
RUNNING_COUNT=$(gcloud run jobs executions list --region=$REGION --project=$PROJECT_ID --format="value(status.conditions[0].status)" --filter="metadata.labels.run.googleapis.com/job~beryl3-qa- AND status.conditions[0].status=True" 2>/dev/null | wc -l)
echo "Currently running executions: $RUNNING_COUNT"

echo ""
echo "Commands:"
echo "---------"
echo "View specific job:     gcloud run jobs describe <job-name> --region=$REGION --project=$PROJECT_ID"
echo "Execute job:           ./workflows/bin/run-job.sh <job-name>"
echo "Delete job:            ./workflows/bin/delete-job.sh <job-name>"
echo "Deploy all jobs:       ./workflows/bin/deploy-qa-jobs.sh"