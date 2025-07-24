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

# Phony targets: these targets do not produce an output file with the same name.
# This prevents conflicts if a file with the same name as the target exists.
.PHONY: all build-css run-dev-server clean makemigrations migrate help

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
