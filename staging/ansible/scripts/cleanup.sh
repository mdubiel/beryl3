#!/bin/bash
# Cleanup script for Ansible staging deployments
# This script removes all containers, images, networks, and data from previous deployments

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANSIBLE_DIR="$(dirname "$SCRIPT_DIR")"
INVENTORY_FILE="$ANSIBLE_DIR/inventory/staging.yml"

echo "🧹 Starting cleanup of staging environment..."

# Function to run ansible command
run_ansible() {
    ansible "$@" -i "$INVENTORY_FILE" -u ansible
}

# Function to run ansible-playbook command
run_ansible_playbook() {
    ansible-playbook "$@" -i "$INVENTORY_FILE"
}

echo "📋 Checking current container status..."
run_ansible staging -m shell -a "docker ps -a --format 'table {{.Names}}\t{{.Status}}'" || echo "No containers found or connection failed"

echo ""
echo "🛑 Stopping all running containers..."
CONTAINERS=$(run_ansible staging -m shell -a "docker ps -q" --one-line | grep -o 'stdout.*' | cut -d' ' -f2- || echo "")
if [ -n "$CONTAINERS" ] && [ "$CONTAINERS" != "stdout" ]; then
    echo "Found containers: $CONTAINERS"
    run_ansible staging -m shell -a "docker stop \$(docker ps -q)" || echo "No containers to stop"
else
    echo "No running containers found"
fi

echo ""
echo "🗑️  Removing all containers..."
run_ansible staging -m shell -a "docker container prune -f" || echo "Failed to remove containers"

echo ""
echo "🔗 Removing Docker networks..."
run_ansible staging -m shell -a "docker network rm monitoring projects registry 2>/dev/null || true" || echo "Failed to remove networks"

echo ""
echo "🖼️  Removing unused Docker images..."
run_ansible staging -m shell -a "docker image prune -a -f" || echo "Failed to remove images"

echo ""
echo "💽 Removing Docker volumes..."
run_ansible staging -m shell -a "docker volume prune -f" || echo "Failed to remove volumes"

echo ""
echo "🧹 Running system-wide Docker cleanup..."
run_ansible staging -m shell -a "docker system prune -a -f --volumes" || echo "Failed to run system cleanup"

echo ""
echo "📁 Cleaning up data directories..."
run_ansible staging -m shell -a "sudo rm -rf /opt/shared/*" || echo "Failed to clean data directories"

echo ""
echo "📁 Recreating base directories..."
run_ansible staging -m file -a "path=/opt/shared state=directory owner=ansible group=docker mode=0755" || echo "Failed to recreate directories"

echo ""
echo "🔍 Final verification - checking for remaining containers..."
run_ansible staging -m shell -a "docker ps -a" || echo "Unable to check containers"

echo ""
echo "🔍 Checking remaining networks..."
run_ansible staging -m shell -a "docker network ls" || echo "Unable to check networks"

echo ""
echo "🔍 Checking disk usage..."
run_ansible staging -m shell -a "df -h /" || echo "Unable to check disk usage"

echo ""
echo "✅ Cleanup completed!"
echo ""
echo "📝 Next steps:"
echo "   1. Run infrastructure deployment: ansible-playbook -i inventory/staging.yml playbooks/infra.yml"
echo "   2. Run full deployment: ansible-playbook -i inventory/staging.yml playbooks/site.yml"
echo "   3. Check services: ansible-playbook -i inventory/staging.yml playbooks/infra.yml --tags verify"
echo ""