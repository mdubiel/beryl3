#!/bin/bash
# Task 65 Phase 2 - Patch template rendering optimizations on production
# This applies the template rendering fixes without full deployment

set -e

echo "=========================================="
echo "Task 65 Phase 2: Template Rendering Patch"
echo "=========================================="
echo ""

PROD_DIR="/home/mdubiel/beryl3"
BACKUP_DIR="/home/mdubiel/beryl3/backups/task65_phase2_$(date +%Y%m%d_%H%M%S)"

echo "Creating backup directory: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# Backup files
echo "Backing up files..."
cp "$PROD_DIR/templates/partials/_item_public_card.html" "$BACKUP_DIR/"
cp "$PROD_DIR/templates/partials/_item_image_lazy.html" "$BACKUP_DIR/"
cp "$PROD_DIR/web/views/public.py" "$BACKUP_DIR/"

echo "✅ Backup created"
echo ""

# Copy new files
echo "Copying updated files from local..."
echo "Please run these commands on your local machine:"
echo ""
echo "scp webapp/templates/partials/_item_public_card.html mdubiel@s30:$PROD_DIR/templates/partials/"
echo "scp webapp/templates/partials/_item_image_lazy.html mdubiel@s30:$PROD_DIR/templates/partials/"
echo "scp webapp/web/views/public.py mdubiel@s30:$PROD_DIR/web/views/"
echo ""
echo "After copying, restart the service:"
echo "sudo systemctl restart beryl3-service"
echo ""
echo "To rollback if needed:"
echo "cp $BACKUP_DIR/* $PROD_DIR/templates/partials/"
echo "cp $BACKUP_DIR/public.py $PROD_DIR/web/views/"
echo "sudo systemctl restart beryl3-service"
