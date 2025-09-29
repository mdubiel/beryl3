# Makefile for managing common project tasks for Beryl

# Variables for commands and paths
TAILWIND_CLI = npx @tailwindcss/cli
TAILWIND_INPUT_CSS = src/input.css
TAILWIND_INPUT_ADMIN_CSS = src/input-admin.css
TAILWIND_OUTPUT_CSS = static/css/tailwind.css
TAILWIND_OUTPUT_ADMIN_CSS = static/css/tailwind-admin.css

PYTHON = python
MANAGE_PY = uv run $(PYTHON) manage.py
SERVER_ADDRESS = 0.0.0.0:8000

# Version management
VERSION_FILE = VERSION
MAJOR = $(shell grep '^MAJOR=' $(VERSION_FILE) | cut -d'=' -f2)
MINOR = $(shell grep '^MINOR=' $(VERSION_FILE) | cut -d'=' -f2)
BUILD = $(shell grep '^BUILD=' $(VERSION_FILE) | cut -d'=' -f2)
VERSION = $(MAJOR).$(MINOR).$(BUILD)

# Docker variables
DOCKER_IMAGE_NAME = beryl3-webapp
DOCKER_TAG = $(VERSION)

# Legacy staging registry (removed)
# DOCKER_REGISTRY = 192.168.1.14:5000
# DOCKER_NAMESPACE = mdubiel.org
# DOCKER_REGISTRY_IMAGE = $(DOCKER_REGISTRY)/$(DOCKER_NAMESPACE)/$(DOCKER_IMAGE_NAME):$(DOCKER_TAG)

# Google Artifact Registry (for QA/Production)
GCP_PROJECT_ID ?= beryl3
GCP_REGION ?= europe-west6
GAR_REPOSITORY ?= beryl3
GAR_REGISTRY = $(GCP_REGION)-docker.pkg.dev
GAR_IMAGE = $(GAR_REGISTRY)/$(GCP_PROJECT_ID)/$(GAR_REPOSITORY)/$(DOCKER_IMAGE_NAME):$(DOCKER_TAG)
GAR_IMAGE_LATEST = $(GAR_REGISTRY)/$(GCP_PROJECT_ID)/$(GAR_REPOSITORY)/$(DOCKER_IMAGE_NAME):latest

# Phony targets: these targets do not produce an output file with the same name.
# This prevents conflicts if a file with the same name as the target exists.
.PHONY: all build-css run-dev-server clean makemigrations migrate help docker-build version-info bump-build bump-minor bump-major gcp-auth gcp-push gcp-deploy gcp-info qa-db-setup qa-db-status qa-start qa-shutdown qa-deploy qa-deploy-with-probe qa-cloudrun-deploy qa-cloudrun-update qa-cloudrun-logs qa-cloudrun-info qa-cloudrun-scale qa-cloudrun-traffic qa-cloudrun-rollback qa-cloudrun-delete qa-status dje-pre-verify-env dje-pre-migrate dje-pre-setup-initial-users dje-pre-setup-site dje-pre-seed dje-pre-collectstatic dje-pre-test-email dje-pre-send-queued-mail dje-pre-deploy-all dje-pre-status dje-pre-setup-logrotate dje-pre-setup-cron dje-pre-setup-services

# Default target: executed when you run 'make' without specifying a target.
# It depends on 'build-css', so it will build the CSS.
all: help

# Target to build Tailwind CSS
build-css:
	@echo "Building Tailwind CSS: $(TAILWIND_INPUT_CSS) -> $(TAILWIND_OUTPUT_CSS)..."
	$(TAILWIND_CLI) -i $(TAILWIND_INPUT_CSS) -o $(TAILWIND_OUTPUT_CSS)
	@echo "Tailwind CSS build complete."
build-css-watch:
	@echo "Building Tailwind CSS: $(TAILWIND_INPUT_CSS) -> $(TAILWIND_OUTPUT_CSS)..."
	$(TAILWIND_CLI) -i $(TAILWIND_INPUT_CSS) -o $(TAILWIND_OUTPUT_CSS) -w
	@echo "Tailwind CSS build complete."
build-admin-css:
	@echo "Building Tailwind CSS: $(TAILWIND_INPUT_ADMIN_CSS) -> $(TAILWIND_OUTPUT_ADMIN_CSS)..."
	$(TAILWIND_CLI) -i $(TAILWIND_INPUT_ADMIN_CSS) -o $(TAILWIND_OUTPUT_ADMIN_CSS)
	@echo "Tailwind CSS build complete."
build-admin-css-watch:
	@echo "Building Tailwind CSS: $(TAILWIND_INPUT_ADMIN_CSS) -> $(TAILWIND_OUTPUT_ADMIN_CSS)..."
	$(TAILWIND_CLI) -i $(TAILWIND_INPUT_ADMIN_CSS) -o $(TAILWIND_OUTPUT_ADMIN_CSS) -w
	@echo "Tailwind CSS build complete."
# Target to run the Django development server
run-dev-server:
	@echo "Starting Django development server at http://$(SERVER_ADDRESS)/..."
	$(MANAGE_PY) runserver ${SERVER_ADDRESS}
# Target to create Django database migrations
makemigrations:
	@echo "Creating Django database migrations..."
	$(MANAGE_PY) makemigrations

# Target to apply Django database migrations
migrate:
	@echo "Applying Django database migrations..."
	$(MANAGE_PY) migrate

# Target to clean generated files (e.g., the compiled CSS)
clean:
	@echo "--- Cleaning up generated files ---"
	@echo "Removing Python __pycache__ directories..."
	find . \( -path "./venv" -o -path "./.venv" -o -path "./.git" \) -prune -o -type d -name "__pycache__" -exec rm -rf {} +

	@echo "Removing Python .pyc files..."
	find . \( -path "./venv" -o -path "./.venv" -o -path "./.git" \) -prune -o -type f -name "*.pyc" -delete

	@echo "Removing common editor backup files (*~, *.swp)..."
	find . \( -path "./venv" -o -path "./.venv" -o -path "./.git" \) -prune -o \( -name "*~" -o -name "*.swp" \) -type f -delete

	@echo "--- Clean complete ---"

# Target to display help information about make targets
help: ## Display this help message
	@echo "Available make targets:"
	@grep -E '^[a-zA-Z0-9_.-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' | sort

# Version management targets
version-info: ## Display current version information
	@echo "Current version: $(VERSION)"
	@echo "Major: $(MAJOR)"
	@echo "Minor: $(MINOR)"
	@echo "Build: $(BUILD)"
	@echo "Docker image: $(DOCKER_IMAGE_NAME):$(DOCKER_TAG)"

bump-build: ## Increment build version (x.y.Z+1)
	@echo "Bumping build version from $(BUILD) to $$(($(BUILD)+1))"
	@sed -i "s/^BUILD=.*/BUILD=$$(($(BUILD)+1))/" $(VERSION_FILE)
	@echo "New version: $$(grep '^MAJOR=' $(VERSION_FILE) | cut -d'=' -f2).$$(grep '^MINOR=' $(VERSION_FILE) | cut -d'=' -f2).$$(grep '^BUILD=' $(VERSION_FILE) | cut -d'=' -f2)"

bump-minor: ## Increment minor version and reset build (x.Y+1.0)
	@echo "Bumping minor version from $(MINOR) to $$(($(MINOR)+1)), resetting build to 0"
	@sed -i "s/^MINOR=.*/MINOR=$$(($(MINOR)+1))/" $(VERSION_FILE)
	@sed -i "s/^BUILD=.*/BUILD=0/" $(VERSION_FILE)
	@echo "New version: $$(grep '^MAJOR=' $(VERSION_FILE) | cut -d'=' -f2).$$(grep '^MINOR=' $(VERSION_FILE) | cut -d'=' -f2).$$(grep '^BUILD=' $(VERSION_FILE) | cut -d'=' -f2)"

bump-major: ## Increment major version and reset minor/build (X+1.0.0)
	@echo "Bumping major version from $(MAJOR) to $$(($(MAJOR)+1)), resetting minor and build to 0"
	@sed -i "s/^MAJOR=.*/MAJOR=$$(($(MAJOR)+1))/" $(VERSION_FILE)
	@sed -i "s/^MINOR=.*/MINOR=0/" $(VERSION_FILE)
	@sed -i "s/^BUILD=.*/BUILD=0/" $(VERSION_FILE)
	@echo "New version: $$(grep '^MAJOR=' $(VERSION_FILE) | cut -d'=' -f2).$$(grep '^MINOR=' $(VERSION_FILE) | cut -d'=' -f2).$$(grep '^BUILD=' $(VERSION_FILE) | cut -d'=' -f2)"

# Docker targets
docker-build: bump-build ## Build Docker image for containerized deployment (auto-increments build version)
	@echo "Building Docker image: $(DOCKER_IMAGE_NAME):$(DOCKER_TAG)"
	docker build -t $(DOCKER_IMAGE_NAME):$(DOCKER_TAG) .
	@echo "Docker image built successfully!"
	@echo "Image: $(DOCKER_IMAGE_NAME):$(DOCKER_TAG)"

# Legacy staging docker targets removed
# docker-push: Build and push to staging registry (removed)
# docker-deploy: Deployment information (removed)

# =====================================
# GOOGLE CLOUD ARTIFACT REGISTRY
# =====================================

gcp-info: ## Display Google Cloud registry configuration
	@echo "=== GOOGLE CLOUD ARTIFACT REGISTRY CONFIGURATION ==="
	@echo "Project ID: $(GCP_PROJECT_ID)"
	@echo "Region: $(GCP_REGION)"
	@echo "Repository: $(GAR_REPOSITORY)"
	@echo "Registry: $(GAR_REGISTRY)"
	@echo "Image: $(GAR_IMAGE)"
	@echo "Latest: $(GAR_IMAGE_LATEST)"
	@echo "=== SETUP REQUIRED ==="
	@echo "1. Set GCP_PROJECT_ID: make gcp-push GCP_PROJECT_ID=your-project-id"
	@echo "2. Authenticate: make gcp-auth"
	@echo "3. Create repository: gcloud artifacts repositories create $(GAR_REPOSITORY) --repository-format=docker --location=$(GCP_REGION)"
	@echo "4. Configure Docker: gcloud auth configure-docker $(GAR_REGISTRY)"

gcp-auth: ## Authenticate Docker with Google Artifact Registry
	@echo "Authenticating Docker with Google Artifact Registry..."
	@if ! command -v gcloud >/dev/null 2>&1; then \
		echo "❌ Error: gcloud CLI not found. Please install Google Cloud SDK."; \
		echo "   Visit: https://cloud.google.com/sdk/docs/install"; \
		exit 1; \
	fi
	@echo "Configuring Docker for Artifact Registry..."
	gcloud auth configure-docker $(GAR_REGISTRY) --quiet
	@echo "✅ Docker authenticated with Google Artifact Registry"

gcp-push: docker-build gcp-auth ## Build and push Docker image to Google Artifact Registry
	@echo "=== PUSHING TO GOOGLE ARTIFACT REGISTRY ==="
	@echo "Tagging image for GAR: $(GAR_IMAGE)"
	docker tag $(DOCKER_IMAGE_NAME):$(DOCKER_TAG) $(GAR_IMAGE)
	@echo "Tagging latest: $(GAR_IMAGE_LATEST)"
	docker tag $(DOCKER_IMAGE_NAME):$(DOCKER_TAG) $(GAR_IMAGE_LATEST)
	@echo "Pushing versioned image: $(GAR_IMAGE)"
	docker push $(GAR_IMAGE)
	@echo "Pushing latest image: $(GAR_IMAGE_LATEST)"
	docker push $(GAR_IMAGE_LATEST)
	@echo "✅ Docker images pushed successfully to Google Artifact Registry!"
	@echo "=== DEPLOYED IMAGES ==="
	@echo "Versioned: $(GAR_IMAGE)"
	@echo "Latest: $(GAR_IMAGE_LATEST)"

gcp-deploy: gcp-push ## Build, push to GAR, and display deployment information
	@echo "=== GOOGLE CLOUD DEPLOYMENT INFORMATION ==="
	@echo "Project: $(GCP_PROJECT_ID)"
	@echo "Registry: $(GAR_REGISTRY)"
	@echo "Repository: $(GAR_REPOSITORY)"
	@echo "Versioned Image: $(GAR_IMAGE)"
	@echo "Latest Image: $(GAR_IMAGE_LATEST)"
	@echo "=== USAGE ==="
	@echo "To deploy this image in GCP, use:"
	@echo "docker run -d -p 8000:8000 --env-file .env $(GAR_IMAGE)"
	@echo "=== KUBERNETES DEPLOYMENT ==="
	@echo "Update your Kubernetes manifests to use: $(GAR_IMAGE)"
	@echo "=== CLOUD RUN DEPLOYMENT ==="
	@echo "gcloud run deploy beryl3-webapp --image=$(GAR_IMAGE) --region=$(GCP_REGION)"

# =====================================
# QA ENVIRONMENT MANAGEMENT
# =====================================

qa-db-setup: ## Setup QA database (beryl3-qa) in GCP and generate qa.env
	@echo "🔧 Setting up QA database environment..."
	@echo "Project: $(GCP_PROJECT_ID)"
	@echo "Region: $(GCP_REGION)"
	./workflows/bin/setup_qa_database.py

qa-db-status: ## Check QA database status and connection info
	@echo "📊 Checking QA database status..."
	@if [ -f ../qa/qa.env ]; then \
		echo "✅ QA configuration found:"; \
		grep -E "^(PG_DB|PG_USER|PG_HOST|DB_INSTANCE_NAME)=" ../qa/qa.env; \
		echo ""; \
		echo "Database status:"; \
		gcloud sql instances describe $$(grep "DB_INSTANCE_NAME=" ../qa/qa.env | cut -d'=' -f2) \
			--project=$(GCP_PROJECT_ID) \
			--format="table(name,state,connectionName,ipAddresses[0].ipAddress)"; \
	else \
		echo "❌ QA environment not configured. Run 'make qa-db-setup' first."; \
	fi

qa-start: ## Start QA environment (database and services)
	@echo "🚀 Starting QA environment..."
	./workflows/bin/manage_database.py start

qa-shutdown: ## Shutdown QA environment to save costs (requires confirmation)
	@echo "⚠️  This will shutdown the QA environment to save costs!"
	@echo "Database and services will become unavailable."
	@echo ""
	@echo "To confirm shutdown, run:"
	@echo "make qa-shutdown-confirmed"

qa-shutdown-confirmed: ## Shutdown QA environment (confirmed)
	@echo "🛑 Shutting down QA environment..."
	./workflows/bin/manage_database.py stop

qa-deploy: ## Deploy complete QA environment (database → storage → application)
	@echo "Deploying complete QA environment with proper dependency order..."
	@echo "Phase 1: Checking database status..."
	@/home/mdubiel/google-cloud-sdk/bin/gcloud sql instances describe beryl3-qa --project=beryl3 --format="value(state)" || echo "Database check failed"
	@echo "Phase 2: Checking storage accessibility..."
	@gsutil ls gs://beryl3-qa-bucket/ > /dev/null && echo "Storage accessible" || echo "Storage check failed"
	@echo "Phase 3: Building and pushing Docker image..."
	docker build -t europe-west6-docker.pkg.dev/beryl3/beryl3/beryl3-webapp:latest -f Dockerfile .
	docker push europe-west6-docker.pkg.dev/beryl3/beryl3/beryl3-webapp:latest
	@echo "Phase 4: Deploying to Cloud Run..."
	/home/mdubiel/google-cloud-sdk/bin/gcloud run services replace cloudrun-qa.yaml --region=europe-west4 --project=beryl3
	/home/mdubiel/google-cloud-sdk/bin/gcloud run services add-iam-policy-binding beryl3-qa-webapp --region=europe-west4 --member="allUsers" --role="roles/run.invoker" --project=beryl3 || echo "IAM binding may already exist"
	@echo "QA environment deployment complete!"

qa-deploy-with-probe: ## Deploy QA environment with startup probe enabled
	@echo "🚀 Deploying QA environment with startup probe enabled..."
	@echo "Phase 1: Checking database status..."
	@/home/mdubiel/google-cloud-sdk/bin/gcloud sql instances describe beryl3-qa --project=beryl3 --format="value(state)" || echo "Database check failed"
	@echo "Phase 2: Checking storage accessibility..."
	@gsutil ls gs://beryl3-qa-bucket/ > /dev/null && echo "✅ Storage accessible" || echo "❌ Storage check failed"
	@echo "Phase 3: Building and pushing Docker image..."
	docker build -t europe-west6-docker.pkg.dev/beryl3/beryl3/beryl3-webapp:latest -f Dockerfile .
	docker push europe-west6-docker.pkg.dev/beryl3/beryl3/beryl3-webapp:latest
	@echo "Phase 4: Deploying to Cloud Run (with startup probe)..."
	./workflows/bin/deploy_webapp.py || echo "Cloud Run service deployment failed"
	/home/mdubiel/google-cloud-sdk/bin/gcloud run services replace /tmp/cloudrun-service-beryl3-qa-webapp.yaml --region=europe-west6 --project=beryl3
	/home/mdubiel/google-cloud-sdk/bin/gcloud run services add-iam-policy-binding beryl3-qa-webapp --region=europe-west6 --member="allUsers" --role="roles/run.invoker" --project=beryl3 || echo "IAM binding may already exist"
	@echo "✅ QA environment deployment complete!"
	@echo "🌐 Service URL: https://beryl3-qa-webapp-530535520412.europe-west6.run.app"

qa-cloudrun-deploy: ## Deploy application only to Google Cloud Run (QA)
	@echo "🚀 Deploying Beryl3 to Google Cloud Run (QA environment)..."
	@echo "Building and pushing Docker image..."
	./workflows/bin/build_images.py
	./workflows/bin/push_images.py
	./workflows/bin/deploy_webapp.py

qa-cloudrun-update: ## Update Cloud Run service with new image version
	@echo "🔄 Updating Cloud Run service with new version..."
	@if [ -z "$(TAG)" ]; then \
		echo "❌ Error: TAG variable is required. Usage: make qa-cloudrun-update TAG=v1.0.1"; \
		exit 1; \
	fi
	./workflows/bin/deploy_new_version.py $(TAG)

qa-cloudrun-logs: ## View Cloud Run service logs
	@echo "📋 Showing Cloud Run service logs..."
	gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=beryl3-qa-webapp" \
		--project=$(GCP_PROJECT_ID) \
		--limit=50 \
		--format="table(timestamp,severity,jsonPayload.message)" \
		--freshness=1h

qa-cloudrun-info: ## Show Cloud Run service information
	@echo "ℹ️  Cloud Run service information:"
	@gcloud run services describe beryl3-qa-webapp \
		--region=$(GCP_REGION) \
		--project=$(GCP_PROJECT_ID) \
		--format="table(metadata.name,status.url,status.conditions[0].status,spec.template.spec.containers[0].image)"

qa-cloudrun-scale: ## Scale Cloud Run service (usage: make qa-cloudrun-scale INSTANCES=2)
	@if [ -z "$(INSTANCES)" ]; then \
		echo "❌ Error: INSTANCES variable is required. Usage: make qa-cloudrun-scale INSTANCES=2"; \
		exit 1; \
	fi
	@echo "📈 Scaling Cloud Run service to $(INSTANCES) instances..."
	gcloud run services update beryl3-qa-webapp \
		--region=$(GCP_REGION) \
		--project=$(GCP_PROJECT_ID) \
		--min-instances=$(INSTANCES) \
		--max-instances=$(INSTANCES)

qa-cloudrun-traffic: ## Manage traffic allocation (usage: make qa-cloudrun-traffic REVISION=beryl3-qa-webapp-xxxxx PERCENT=100)
	@if [ -z "$(REVISION)" ] || [ -z "$(PERCENT)" ]; then \
		echo "❌ Error: REVISION and PERCENT variables are required."; \
		echo "Usage: make qa-cloudrun-traffic REVISION=beryl3-qa-webapp-xxxxx PERCENT=100"; \
		exit 1; \
	fi
	@echo "🔀 Routing $(PERCENT)% traffic to revision $(REVISION)..."
	gcloud run services update-traffic beryl3-qa-webapp \
		--region=$(GCP_REGION) \
		--project=$(GCP_PROJECT_ID) \
		--to-revisions=$(REVISION)=$(PERCENT)

qa-cloudrun-rollback: ## Rollback to previous revision
	@echo "⏪ Rolling back to previous revision..."
	gcloud run services update-traffic beryl3-qa-webapp \
		--region=$(GCP_REGION) \
		--project=$(GCP_PROJECT_ID) \
		--to-latest=100

qa-cloudrun-delete: ## Delete Cloud Run service (DESTRUCTIVE)
	@echo "⚠️  This will permanently delete the Cloud Run service!"
	@read -p "Are you sure? Type 'yes' to continue: " confirm && [ "$$confirm" = "yes" ] || exit 1
	@echo "🗑️  Deleting Cloud Run service..."
	gcloud run services delete beryl3-qa-webapp \
		--region=$(GCP_REGION) \
		--project=$(GCP_PROJECT_ID) \
		--quiet

qa-status: ## Show comprehensive QA environment status
	@echo "=== QA ENVIRONMENT STATUS ==="
	@if [ -f ../qa/qa.env ]; then \
		echo "✅ Configuration: Found"; \
		echo "📊 Database Status:"; \
		gcloud sql instances describe $$(grep "DB_INSTANCE_NAME=" ../qa/qa.env | cut -d'=' -f2) \
			--project=$(GCP_PROJECT_ID) \
			--format="table(name,state,region,connectionName)" 2>/dev/null || echo "❌ Database not accessible"; \
		echo ""; \
		echo "🪣 Storage Buckets:"; \
		BUCKET_NAME=$$(grep "GCS_BUCKET_NAME=" ../qa/qa.env | cut -d'=' -f2); \
		if [ -n "$$BUCKET_NAME" ]; then \
			echo "Bucket: $$BUCKET_NAME"; \
			gsutil ls -L -b gs://$$BUCKET_NAME 2>/dev/null | grep -E "(Creation time|Location|Storage class|Size)" || echo "❌ Bucket not accessible"; \
			echo "Folder structure:"; \
			gsutil ls gs://$$BUCKET_NAME/**/.keep 2>/dev/null | sed 's|gs://[^/]*/||' | sed 's|/.keep||' | sort || echo "No folders found"; \
		else \
			echo "❌ No bucket configured"; \
		fi; \
		echo ""; \
		echo "☁️  Cloud Run Services:"; \
		gcloud run services list --project=$(GCP_PROJECT_ID) --region=$(GCP_REGION) \
			--filter="metadata.labels.environment=qa OR metadata.name~beryl3-qa" \
			--format="table(metadata.name,status.url,status.conditions[0].status,spec.template.metadata.annotations.autoscaling\.knative\.dev/minScale,spec.template.metadata.annotations.autoscaling\.knative\.dev/maxScale)" 2>/dev/null || echo "No services found"; \
		echo ""; \
		echo "💻 GCE Instances:"; \
		gcloud compute instances list --project=$(GCP_PROJECT_ID) \
			--filter="labels.environment=qa OR name~beryl3-qa" \
			--format="table(name,status,zone,machineType.scope(machineTypes))" 2>/dev/null || echo "No instances found"; \
	else \
		echo "❌ QA environment not configured. Run 'make qa-db-setup' first."; \
	fi

# =====================================
# STAGING ENVIRONMENT REMOVED
# =====================================
# All staging infrastructure and application management targets have been removed.
# The staging environment (192.168.1.14) has been decommissioned.
# Use QA environment targets (qa-*) for testing and development.

# =====================================
# DJANGO EUROPE PREPROD ENVIRONMENT
# =====================================

# Django Europe preprod configuration
DJE_PRE_HOST = mdubiel@148.251.140.153
DJE_PRE_PATH = /home/mdubiel/beryl3-preprod
DJE_PRE_ENV_FILE = $(DJE_PRE_PATH)/.env

dje-pre-verify-env: ## Verify Django Europe preprod environment variables are loaded
	@echo "🔍 Verifying Django Europe preprod environment variables..."
	@ssh $(DJE_PRE_HOST) 'cd $(DJE_PRE_PATH) && \
		if [ ! -f .env ]; then \
			echo "❌ .env file not found at $(DJE_PRE_PATH)/.env"; \
			exit 1; \
		fi; \
		echo "✅ .env file found"; \
		echo "🔧 Verifying critical environment variables..."; \
		source .env && \
		for var in DEBUG SECRET_KEY DATABASE_URL ALLOWED_HOSTS USE_GCS_STORAGE GCS_BUCKET_NAME; do \
			if [ -z "$${!var}" ]; then \
				echo "❌ Missing required variable: $$var"; \
				exit 1; \
			else \
				echo "✅ $$var: $${!var}"; \
			fi; \
		done; \
		echo "🎉 All critical environment variables verified!"'

dje-pre-migrate: dje-pre-verify-env ## Run Django database migrations on Django Europe preprod
	@echo "🔄 Running database migrations on Django Europe preprod..."
	@ssh $(DJE_PRE_HOST) 'cd $(DJE_PRE_PATH) && \
		source .env && \
		uv run python manage.py migrate --noinput && \
		echo "✅ Database migrations completed successfully!"'

dje-pre-setup-initial-users: dje-pre-verify-env ## Setup initial users on Django Europe preprod
	@echo "👥 Setting up initial users on Django Europe preprod..."
	@ssh $(DJE_PRE_HOST) 'cd $(DJE_PRE_PATH) && \
		source .env && \
		uv run python manage.py setup_initial_users && \
		echo "✅ Initial users setup completed!"'

dje-pre-setup-site: dje-pre-verify-env ## Setup Django site configuration on Django Europe preprod
	@echo "🌐 Setting up site configuration on Django Europe preprod..."
	@ssh $(DJE_PRE_HOST) 'cd $(DJE_PRE_PATH) && \
		source .env && \
		uv run python manage.py setup_site && \
		echo "✅ Site configuration completed!"'

dje-pre-seed: dje-pre-verify-env ## Seed initial data on Django Europe preprod
	@echo "🌱 Seeding initial data on Django Europe preprod..."
	@ssh $(DJE_PRE_HOST) 'cd $(DJE_PRE_PATH) && \
		source .env && \
		uv run python manage.py seed_data && \
		echo "✅ Data seeding completed!"'

dje-pre-collectstatic: dje-pre-verify-env ## Collect static files on Django Europe preprod
	@echo "📦 Collecting static files on Django Europe preprod..."
	@ssh $(DJE_PRE_HOST) 'cd $(DJE_PRE_PATH) && \
		source .env && \
		uv run python manage.py collectstatic --noinput --clear && \
		echo "✅ Static files collected successfully!"'

dje-pre-test-email: dje-pre-verify-env ## Send test email on Django Europe preprod
	@echo "📧 Sending test email on Django Europe preprod..."
	@if [ -z "$(EMAIL)" ]; then \
		echo "❌ Error: EMAIL variable is required. Usage: make dje-pre-test-email EMAIL=your@email.com"; \
		exit 1; \
	fi
	@ssh $(DJE_PRE_HOST) 'cd $(DJE_PRE_PATH) && \
		source .env && \
		uv run python manage.py send_test_emails $(EMAIL) 3 --priority now && \
		echo "✅ Test emails sent to $(EMAIL)!"'

dje-pre-send-queued-mail: dje-pre-verify-env ## Process queued emails on Django Europe preprod
	@echo "📬 Processing queued emails on Django Europe preprod..."
	@ssh $(DJE_PRE_HOST) 'cd $(DJE_PRE_PATH) && \
		source .env && \
		uv run python manage.py send_queued_mail && \
		echo "✅ Queued emails processed!"'

dje-pre-deploy-all: dje-pre-verify-env ## Run full deployment sequence on Django Europe preprod
	@echo "🚀 Running full deployment sequence on Django Europe preprod..."
	@echo "Step 1/4: Database migrations..."
	@$(MAKE) dje-pre-migrate
	@echo "Step 2/4: Site setup..."
	@$(MAKE) dje-pre-setup-site
	@echo "Step 3/4: Static files collection..."
	@$(MAKE) dje-pre-collectstatic
	@echo "Step 4/4: Restarting service..."
	@ssh $(DJE_PRE_HOST) 'cd $(DJE_PRE_PATH) && ./restart.sh'
	@echo "✅ Full deployment completed on Django Europe preprod!"
	@echo "🌐 Service available at: http://148.251.140.153/"

dje-pre-status: ## Show Django Europe preprod environment status
	@echo "=== DJANGO EUROPE PREPROD STATUS ==="
	@echo "Host: $(DJE_PRE_HOST)"
	@echo "Path: $(DJE_PRE_PATH)"
	@echo ""
	@echo "📊 Service Status:"
	@ssh $(DJE_PRE_HOST) 'cd $(DJE_PRE_PATH) && \
		if [ -f gunicorn.pid ]; then \
			PID=$$(cat gunicorn.pid); \
			if ps -p $$PID > /dev/null 2>&1; then \
				echo "✅ Gunicorn service running (PID: $$PID)"; \
			else \
				echo "❌ Gunicorn service not running (stale PID file)"; \
			fi; \
		else \
			echo "❌ Gunicorn service not running (no PID file)"; \
		fi; \
		echo ""; \
		echo "📁 Directory Status:"; \
		ls -la $(DJE_PRE_PATH) | head -10; \
		echo ""; \
		echo "🔧 Environment File:"; \
		if [ -f .env ]; then \
			echo "✅ .env file exists"; \
			echo "Environment variables count: $$(grep -c "^[^#]" .env)"; \
		else \
			echo "❌ .env file missing"; \
		fi; \
		echo ""; \
		echo "📋 Recent Log Activity:"; \
		if [ -d logs ]; then \
			echo "Log files:"; \
			ls -la logs/ | tail -5; \
		else \
			echo "No logs directory found"; \
		fi'

dje-pre-setup-logrotate: dje-pre-verify-env ## Setup local logrotate configuration for Django Europe preprod logs
	@echo "🔄 Setting up local logrotate configuration for Django Europe preprod..."
	@ssh $(DJE_PRE_HOST) 'cd $(DJE_PRE_PATH) && \
		echo "Creating workflows directory..."; \
		mkdir -p workflows; \
		echo "Creating local logrotate configuration..."; \
		cat > workflows/logrotate.conf << "EOF"
$(DJE_PRE_PATH)/logs/*.log {
    size 5M
    rotate 5
    compress
    delaycompress
    missingok
    notifempty
    create 644 mdubiel mdubiel
    postrotate
        # Signal gunicorn to reopen log files if running
        if [ -f $(DJE_PRE_PATH)/gunicorn.pid ]; then
            PID=$$(cat $(DJE_PRE_PATH)/gunicorn.pid)
            if ps -p $$PID > /dev/null 2>&1; then
                kill -USR1 $$PID
            fi
        fi
    endscript
}

$(DJE_PRE_PATH)/logs/*.jsonl {
    size 5M
    rotate 5
    compress
    delaycompress
    missingok
    notifempty
    create 644 mdubiel mdubiel
    copytruncate
}
EOF
		echo "✅ Local logrotate configuration created at workflows/logrotate.conf"; \
		echo "Testing logrotate configuration..."; \
		/usr/sbin/logrotate -d workflows/logrotate.conf && \
		echo "✅ Logrotate configuration test passed!" && \
		echo "📋 Manual execution command: /usr/sbin/logrotate -s workflows/logrotate.state workflows/logrotate.conf"'

dje-pre-setup-cron: dje-pre-verify-env ## Setup crontab for email queue processing and log rotation on Django Europe preprod
	@echo "📅 Setting up crontab for email queue processing and log rotation..."
	@ssh $(DJE_PRE_HOST) 'cd $(DJE_PRE_PATH) && \
		echo "Creating cron jobs for email queue and log rotation..."; \
		(crontab -l 2>/dev/null | grep -v -E "(send_queued_mail|logrotate)" || true; \
		echo "*/5 * * * * cd $(DJE_PRE_PATH) && source .env && uv run python manage.py send_queued_mail >> logs/cron.log 2>&1"; \
		echo "0 */6 * * * cd $(DJE_PRE_PATH) && /usr/sbin/logrotate -s workflows/logrotate.state workflows/logrotate.conf >> logs/logrotate.log 2>&1") | crontab -; \
		echo "✅ Crontab configured:"; \
		echo "  - Email queue processing: every 5 minutes"; \
		echo "  - Log rotation: every 6 hours via logrotate"; \
		echo "Current crontab:"; \
		crontab -l | grep -E "(send_queued_mail|logrotate|#)" || echo "No matching cron jobs found"'

dje-pre-setup-services: dje-pre-setup-logrotate dje-pre-setup-cron ## Setup all background services (logrotate + cron) for Django Europe preprod
	@echo "🛠️  Setting up all background services for Django Europe preprod..."
	@echo "✅ Local logrotate configuration created and tested"
	@echo "✅ Crontab configured for email queue processing and log rotation"
	@echo "📊 Service summary:"
	@echo "  - Log rotation: Every 5MB, keep 5 files, compressed (via cron every 6 hours)"
	@echo "  - Email queue: Processed every 5 minutes via cron"
	@echo "  - Configuration: $(DJE_PRE_PATH)/workflows/logrotate.conf"
	@echo "  - Log files: $(DJE_PRE_PATH)/logs/*.log and *.jsonl"
	@echo "  - Manual execution: /usr/sbin/logrotate -s workflows/logrotate.state workflows/logrotate.conf"
	@echo "🎉 All background services configured successfully!"
