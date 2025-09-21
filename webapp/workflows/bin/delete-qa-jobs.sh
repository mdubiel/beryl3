#!/bin/bash
set -e

# Configuration
PROJECT_ID="beryl3"
REGION="europe-west4"

echo "Deleting all beryl3-qa-* Cloud Run Jobs"

# Get list of all beryl3-qa-* jobs
JOBS=$(gcloud run jobs list --region=$REGION --project=$PROJECT_ID --format="value(metadata.name)" --filter="metadata.name~beryl3-qa-")

if [ -z "$JOBS" ]; then
    echo "No beryl3-qa-* jobs found to delete."
    exit 0
fi

echo "Found the following beryl3-qa-* jobs:"
echo "$JOBS" | sed 's/^/  - /'
echo ""

# Confirm deletion
echo "WARNING: Are you sure you want to delete ALL beryl3-qa-* jobs? [y/N]"
read -r confirmation
if [[ ! $confirmation =~ ^[Yy]$ ]]; then
    echo "Deletion cancelled."
    exit 1
fi

# Delete each job
echo "Deleting jobs..."
while IFS= read -r job; do
    if [ -n "$job" ]; then
        echo "  Deleting $job..."
        gcloud run jobs delete $job --region=$REGION --project=$PROJECT_ID --quiet
        echo "  $job deleted"
    fi
done <<< "$JOBS"

echo ""
echo "All beryl3-qa-* jobs deleted successfully!"

# Show remaining jobs (should be empty now)
echo ""
echo "Remaining Cloud Run Jobs:"
gcloud run jobs list --region=$REGION --project=$PROJECT_ID --format="table(metadata.name)" --filter="metadata.name~beryl3-qa-" || echo "  No beryl3-qa-* jobs remaining."