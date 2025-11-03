#!/bin/bash
# Deploy with icon pre-rendering
#
# This script pre-renders lucide icons before deployment to production.
# Icons are rendered once at build time and embedded as static SVG.
#
# Usage:
#   ./workflows/bin/deploy_with_prerendering.sh production
#   ./workflows/bin/deploy_with_prerendering.sh qa

set -e

ENVIRONMENT=${1:-production}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
WEBAPP_DIR="$PROJECT_ROOT/webapp"

echo "========================================"
echo "Deployment with Icon Pre-rendering"
echo "========================================"
echo "Environment: $ENVIRONMENT"
echo "Project root: $PROJECT_ROOT"
echo ""

# Step 1: Clean previous compiled templates
echo "→ Cleaning previous compiled templates..."
rm -rf "$WEBAPP_DIR/templates_compiled"

# Step 2: Pre-render lucide icons
echo "→ Pre-rendering lucide icons..."
cd "$WEBAPP_DIR"
python workflows/bin/prerender_lucide_icons.py \
    --template-dir templates \
    --output-dir templates_compiled

if [ ! -d "$WEBAPP_DIR/templates_compiled" ]; then
    echo "ERROR: Pre-rendering failed - compiled templates not found"
    exit 1
fi

echo ""
echo "✅ Pre-rendering complete"
echo ""

# Step 3: Deploy based on environment
case "$ENVIRONMENT" in
    "production"|"prod")
        echo "→ Deploying to Django Europe production..."
        cd "$PROJECT_ROOT"
        make dje-prod-deploy-all
        ;;
    "preprod"|"pre")
        echo "→ Deploying to Django Europe preprod..."
        cd "$PROJECT_ROOT"
        make dje-pre-deploy-all
        ;;
    "qa")
        echo "→ Deploying to Google Cloud Run QA..."
        cd "$WEBAPP_DIR"
        python workflows/bin/deploy_webapp.py --env qa
        ;;
    *)
        echo "ERROR: Unknown environment: $ENVIRONMENT"
        echo "Valid options: production, preprod, qa"
        exit 1
        ;;
esac

echo ""
echo "========================================"
echo "✅ Deployment complete!"
echo "========================================"
echo ""
echo "Deployed with pre-rendered icons:"
echo "  - Zero runtime template tag overhead"
echo "  - Icons embedded as static SVG"
echo "  - Expected improvement: 20-40% faster"
echo ""
