#!/bin/bash
set -e

# Configuration
PROJECT_ID="beryl3"
REGION="europe-west4"
SERVICE_ACCOUNT="beryl3-qa-storage@beryl3.iam.gserviceaccount.com"
IMAGE="europe-west6-docker.pkg.dev/beryl3/beryl3/beryl3-jobs:latest"

# Common secrets for all jobs
COMMON_SECRETS="SECRET_KEY=beryl3-qa-secret-key:latest,DEBUG=beryl3-qa-debug:latest,ALLOWED_HOSTS=beryl3-qa-allowed-hosts:latest,SITE_DOMAIN=beryl3-qa-site-domain:latest,USE_GCS_STORAGE=beryl3-qa-use-gcs-storage:latest,GCS_BUCKET_NAME=beryl3-qa-gcs-bucket-name:latest,GCS_PROJECT_ID=beryl3-qa-gcs-project-id:latest,GCS_LOCATION=beryl3-qa-gcs-location:latest,STATIC_URL=beryl3-qa-static-url:latest,MEDIA_URL=beryl3-qa-media-url:latest,ENVIRONMENT=beryl3-qa-environment:latest,DEPLOYMENT_ENVIRONMENT=beryl3-qa-deployment-environment:latest,APPLICATION_ACTIVITY_LOGGING=beryl3-qa-application-activity-logging:latest,PG_DB=beryl3-qa-pg-db:latest,PG_USER=beryl3-qa-pg-user:latest,PG_PASSWORD=beryl3-qa-pg-password:latest,PG_HOST=beryl3-qa-pg-host-jobs:latest,PG_PORT=beryl3-qa-pg-port:latest,DB_ENGINE=beryl3-qa-db-engine:latest"

echo "Deploying beryl3-qa-* Cloud Run Jobs"
echo "Using image: $IMAGE"
echo ""

# Function to deploy a job
deploy_job() {
    local job_name=$1
    local command=$2
    local description=$3
    
    echo "Deploying $job_name ($description)..."
    gcloud run jobs deploy $job_name \
      --image=$IMAGE \
      --command="$command" \
      --region=$REGION \
      --service-account=$SERVICE_ACCOUNT \
      --set-secrets="$COMMON_SECRETS" \
      --set-cloudsql-instances="beryl3:europe-west6:beryl3-qa" \
      --project=$PROJECT_ID
    echo "  $job_name deployed successfully"
    echo ""
}

# Deploy all QA jobs
echo "Deploying Cloud Run Jobs..."
echo ""

deploy_job "beryl3-qa-migrate" "uv,run,python,manage.py,migrate,--noinput" "Database migrations"

deploy_job "beryl3-qa-collectstatic" "uv,run,python,manage.py,collectstatic,--noinput,--clear" "Collect static files"

deploy_job "beryl3-qa-seed" "uv,run,python,manage.py,seed_data" "Seed initial data"

deploy_job "beryl3-qa-setup-initial-users" "uv,run,python,manage.py,setup_initial_users" "Setup initial users"

echo "All beryl3-qa-* jobs deployed successfully!"
echo ""
echo "Deployed jobs:"
gcloud run jobs list --region=$REGION --project=$PROJECT_ID --format="table(metadata.name,status.conditions[0].status)" --filter="metadata.name~beryl3-qa-"
echo ""
echo "Execute jobs with:"
echo "  ./workflows/bin/run-job.sh beryl3-qa-migrate"
echo "  ./workflows/bin/run-job.sh beryl3-qa-collectstatic"
echo "  ./workflows/bin/run-job.sh beryl3-qa-seed"
echo "  ./workflows/bin/run-job.sh beryl3-qa-setup-initial-users"