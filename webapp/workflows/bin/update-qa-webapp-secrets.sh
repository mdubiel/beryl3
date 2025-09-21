#!/bin/bash
set -e

# Configuration
YAML_FILE="cloudrun-qa.yaml"

echo "Updating $YAML_FILE to use secrets instead of hardcoded values..."

# Create a backup
cp $YAML_FILE ${YAML_FILE}.backup

# Replace hardcoded environment variables with secret references
cat > $YAML_FILE << 'EOF'
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: beryl3-qa-webapp
  labels:
    cloud.googleapis.com/location: europe-west4
  annotations:
    run.googleapis.com/ingress: all
    environment: qa
spec:
  template:
    metadata:
      labels:
        environment: qa
        app: beryl3-webapp
      annotations:
        autoscaling.knative.dev/maxScale: "1"
        autoscaling.knative.dev/minScale: "0"
        autoscaling.knative.dev/target: "80"
        run.googleapis.com/cpu: "2000m"
        run.googleapis.com/memory: "2Gi"
        run.googleapis.com/execution-environment: gen2
        run.googleapis.com/service-account: beryl3-qa-storage@beryl3.iam.gserviceaccount.com
        run.googleapis.com/cloudsql-instances: beryl3:europe-west6:beryl3-qa
    spec:
      containerConcurrency: 1
      timeoutSeconds: 600
      serviceAccountName: beryl3-qa-storage@beryl3.iam.gserviceaccount.com
      containers:
      - name: beryl3-webapp
        image: europe-west6-docker.pkg.dev/beryl3/beryl3/beryl3-webapp:latest
        ports:
        - name: http1
          containerPort: 8000
        env:
        # Django Configuration - Using Secrets
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: beryl3-qa-secret-key
              key: latest
        - name: DEBUG
          valueFrom:
            secretKeyRef:
              name: beryl3-qa-debug
              key: latest
        - name: ALLOWED_HOSTS
          valueFrom:
            secretKeyRef:
              name: beryl3-qa-allowed-hosts
              key: latest
        - name: SITE_DOMAIN
          valueFrom:
            secretKeyRef:
              name: beryl3-qa-site-domain
              key: latest
        
        # Database Configuration - Using Secrets
        - name: PG_DB
          valueFrom:
            secretKeyRef:
              name: beryl3-qa-pg-db
              key: latest
        - name: PG_USER
          valueFrom:
            secretKeyRef:
              name: beryl3-qa-pg-user
              key: latest
        - name: PG_PASSWORD
          valueFrom:
            secretKeyRef:
              name: beryl3-qa-pg-password
              key: latest
        - name: PG_HOST
          valueFrom:
            secretKeyRef:
              name: beryl3-qa-pg-host-webapp
              key: latest
        - name: PG_PORT
          valueFrom:
            secretKeyRef:
              name: beryl3-qa-pg-port
              key: latest
        - name: DB_ENGINE
          valueFrom:
            secretKeyRef:
              name: beryl3-qa-db-engine
              key: latest
        
        # Storage Configuration - Using Secrets
        - name: USE_GCS_STORAGE
          valueFrom:
            secretKeyRef:
              name: beryl3-qa-use-gcs-storage
              key: latest
        - name: GCS_BUCKET_NAME
          valueFrom:
            secretKeyRef:
              name: beryl3-qa-gcs-bucket-name
              key: latest
        - name: GCS_PROJECT_ID
          valueFrom:
            secretKeyRef:
              name: beryl3-qa-gcs-project-id
              key: latest
        - name: GCS_LOCATION
          valueFrom:
            secretKeyRef:
              name: beryl3-qa-gcs-location
              key: latest
        - name: STATIC_URL
          valueFrom:
            secretKeyRef:
              name: beryl3-qa-static-url
              key: latest
        - name: MEDIA_URL
          valueFrom:
            secretKeyRef:
              name: beryl3-qa-media-url
              key: latest
        
        # Application Configuration - Using Secrets
        - name: ENVIRONMENT
          valueFrom:
            secretKeyRef:
              name: beryl3-qa-environment
              key: latest
        - name: DEPLOYMENT_ENVIRONMENT
          valueFrom:
            secretKeyRef:
              name: beryl3-qa-deployment-environment
              key: latest
        - name: APPLICATION_ACTIVITY_LOGGING
          valueFrom:
            secretKeyRef:
              name: beryl3-qa-application-activity-logging
              key: latest
        
        # Resource limits
        resources:
          limits:
            cpu: "2000m"
            memory: "2Gi"
          requests:
            cpu: "1000m"
            memory: "1Gi"

  traffic:
  - percent: 100
    latestRevision: true
EOF

echo "Updated $YAML_FILE to use secrets instead of hardcoded values"
echo "Backup saved as ${YAML_FILE}.backup"
echo ""
echo "Key changes:"
echo "- All environment variables now use secretKeyRef"
echo "- PG_HOST uses beryl3-qa-pg-host-webapp secret"
echo "- Removed hardcoded database URL"
echo "- All configuration values come from secrets"
echo ""
echo "Deploy with: ./workflows/bin/deploy-qa-webapp.sh"