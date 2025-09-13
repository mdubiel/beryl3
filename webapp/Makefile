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

# Docker variables
DOCKER_IMAGE_NAME = beryl3-webapp
DOCKER_TAG = latest
DOCKER_REGISTRY = 192.168.1.14:5000
DOCKER_NAMESPACE = mdubiel.org
DOCKER_REGISTRY_IMAGE = $(DOCKER_REGISTRY)/$(DOCKER_NAMESPACE)/$(DOCKER_IMAGE_NAME):$(DOCKER_TAG)

# Phony targets: these targets do not produce an output file with the same name.
# This prevents conflicts if a file with the same name as the target exists.
.PHONY: all build-css run-dev-server clean makemigrations migrate help docker-build docker-push docker-deploy deploy-staging infra-deploy infra-start infra-stop infra-restart app-deploy app-start app-stop app-restart app-logs staging-status

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
	@echo "Building Tailwind CSS: $(TAILWIND_INPUT_ADMIN_CSS) -> $(TAILWIND_OUTPUT__ADMIN_CSS)..."
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

# Docker targets
docker-build: ## Build Docker image for containerized deployment
	@echo "Building Docker image: $(DOCKER_IMAGE_NAME):$(DOCKER_TAG)"
	docker build -t $(DOCKER_IMAGE_NAME):$(DOCKER_TAG) .
	@echo "Docker image built successfully!"

docker-push: docker-build ## Build and push Docker image to staging registry
	@echo "Tagging image for registry: $(DOCKER_REGISTRY_IMAGE)"
	docker tag $(DOCKER_IMAGE_NAME):$(DOCKER_TAG) $(DOCKER_REGISTRY_IMAGE)
	@echo "Pushing image to registry: $(DOCKER_REGISTRY)"
	docker push $(DOCKER_REGISTRY_IMAGE)
	@echo "Docker image pushed successfully!"
	@echo "Image available at: $(DOCKER_REGISTRY_IMAGE)"

docker-deploy: docker-push ## Build, push, and display deployment information
	@echo "=== DEPLOYMENT INFORMATION ==="
	@echo "Docker Image: $(DOCKER_REGISTRY_IMAGE)"
	@echo "Registry URL: http://$(DOCKER_REGISTRY)"
	@echo "Image digest: $$(docker images --digests $(DOCKER_REGISTRY_IMAGE) --format 'table {{.Repository}}:{{.Tag}}\t{{.Digest}}' | tail -n +2)"
	@echo "=== USAGE ==="
	@echo "To deploy this image, use:"
	@echo "docker run -d -p 8000:8000 --env-file .env $(DOCKER_REGISTRY_IMAGE)"
	@echo "=== ANSIBLE DEPLOYMENT ==="
	@echo "Update your ansible playbook to use: $(DOCKER_REGISTRY_IMAGE)"

deploy-staging: ## Deploy application to staging environment (beryl3.staging.mdubiel.org)
	@echo "Deploying Beryl3 to staging environment..."
	@echo "Domain: beryl3.staging.mdubiel.org"
	@echo "Image: $(DOCKER_REGISTRY_IMAGE)"
	cd ../staging/ansible && ansible-playbook -i inventory/staging.yml playbooks/deploy-app.yml

# =====================================
# STAGING INFRASTRUCTURE MANAGEMENT
# =====================================
# Infrastructure: nginx, grafana, loki, prometheus, monitoring tools, registry

infra-deploy: ## Deploy complete staging infrastructure (full setup)
	@echo "🚀 Deploying staging infrastructure (nginx, grafana, loki, prometheus, monitoring, registry)..."
	cd ../staging && ansible-playbook -i ansible/inventory/staging.yml ansible/playbooks/infra-manage.yml -e action=deploy

infra-start: ## Start staging infrastructure services
	@echo "▶️  Starting staging infrastructure services..."
	cd ../staging && ansible-playbook -i ansible/inventory/staging.yml ansible/playbooks/infra-manage.yml -e action=start

infra-stop: ## Stop staging infrastructure services
	@echo "⏹️  Stopping staging infrastructure services..."
	cd ../staging && ansible-playbook -i ansible/inventory/staging.yml ansible/playbooks/infra-manage.yml -e action=stop

infra-restart: ## Restart staging infrastructure services
	@echo "🔄 Restarting staging infrastructure services..."
	cd ../staging && ansible-playbook -i ansible/inventory/staging.yml ansible/playbooks/infra-manage.yml -e action=restart

# =====================================
# STAGING APPLICATION MANAGEMENT
# =====================================
# Application: beryl3 webapp, email worker, postgres, redis

app-deploy: ## Deploy complete beryl3 application (full setup)
	@echo "🚀 Deploying beryl3 application (webapp, email worker, postgres, redis)..."
	cd ../staging && ansible-playbook -i ansible/inventory/staging.yml ansible/playbooks/app-manage.yml -e action=deploy

app-start: ## Start beryl3 application services
	@echo "▶️  Starting beryl3 application services..."
	cd ../staging && ansible-playbook -i ansible/inventory/staging.yml ansible/playbooks/app-manage.yml -e action=start

app-stop: ## Stop beryl3 application services
	@echo "⏹️  Stopping beryl3 application services..."
	cd ../staging && ansible-playbook -i ansible/inventory/staging.yml ansible/playbooks/app-manage.yml -e action=stop

app-restart: ## Restart beryl3 application services
	@echo "🔄 Restarting beryl3 application services..."
	cd ../staging && ansible-playbook -i ansible/inventory/staging.yml ansible/playbooks/app-manage.yml -e action=restart

app-logs: ## Show beryl3 application logs
	@echo "📋 Showing beryl3 application logs..."
	cd ../staging && ansible staging-server -i ansible/inventory/staging.yml -m shell -a "docker logs beryl3-webapp --tail=50"

staging-status: ## Show status of all staging containers with detailed service status
	@echo "=== STAGING ENVIRONMENT STATUS ==="
	@echo "Checking all staging services..."
	@echo
	cd ../staging && ansible staging-server -i ansible/inventory/staging.yml -m shell -a 'echo "=== 🌐 INFRASTRUCTURE SERVICES ==="; echo "SERVICE NAME                   STATUS"; echo "------------------------------------------------"; docker ps -a | grep -E "^[a-z0-9]+.*\s+(nginx-proxy|grafana|loki|prometheus|alertmanager|adminer|registry|cadvisor|node-exporter|promtail|blackbox)" | awk "{if(\$$4 ~ /Up/) status=\"🟢 UP\"; else if(\$$4 ~ /Exited|Exit/) status=\"🔴 DOWN\"; else if(\$$4 ~ /Restart/) status=\"🟡 RESTARTING\"; else status=\"❓ UNKNOWN\"; printf \"%-30s %s\\n\", \$$NF, status}"; echo; echo "=== 🚀 APPLICATION SERVICES ==="; echo "SERVICE NAME                   STATUS"; echo "------------------------------------------------"; docker ps -a | grep -E "^[a-z0-9]+.*\s+beryl3-" | awk "{if(\$$4 ~ /Up/) status=\"🟢 UP\"; else if(\$$4 ~ /Exited|Exit/) status=\"🔴 DOWN\"; else if(\$$4 ~ /Restart/) status=\"🟡 RESTARTING\"; else status=\"❓ UNKNOWN\"; printf \"%-30s %s\\n\", \$$NF, status}"; echo; echo "=== 📊 SUMMARY ==="; TOTAL=$$(docker ps -a | tail -n +2 | wc -l); RUNNING=$$(docker ps | tail -n +2 | wc -l); STOPPED=$$((TOTAL - RUNNING)); echo "Total Services: $$TOTAL"; echo "🟢 Running: $$RUNNING"; echo "🔴 Stopped/Error: $$STOPPED"'
