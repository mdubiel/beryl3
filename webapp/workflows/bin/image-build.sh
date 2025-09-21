#!/bin/bash
set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration
VERSION_FILE="$PROJECT_ROOT/VERSION"
REGISTRY="europe-west6-docker.pkg.dev/beryl3/beryl3"

echo "Building Docker images with version bump..."
echo "Project root: $PROJECT_ROOT"

# Change to project root for Docker build
cd "$PROJECT_ROOT"

# Read current version
if [ ! -f "$VERSION_FILE" ]; then
    echo "VERSION file not found. Creating initial version file..."
    echo "MAJOR=0" > $VERSION_FILE
    echo "MINOR=1" >> $VERSION_FILE
    echo "BUILD=0" >> $VERSION_FILE
fi

# Source the version file
source $VERSION_FILE

# Increment build number
BUILD=$((BUILD + 1))

# Update VERSION file
cat > $VERSION_FILE << EOF
MAJOR=$MAJOR
MINOR=$MINOR
BUILD=$BUILD
EOF

# Create version string
VERSION_TAG="$MAJOR.$MINOR.$BUILD"
echo "New version: $VERSION_TAG"

# Build webapp image
echo "Building webapp image..."
docker build --target webapp -t beryl3-webapp:$VERSION_TAG -t beryl3-webapp:latest .
docker tag beryl3-webapp:$VERSION_TAG $REGISTRY/beryl3-webapp:$VERSION_TAG
docker tag beryl3-webapp:latest $REGISTRY/beryl3-webapp:latest

# Build jobs image  
echo "Building jobs image..."
docker build --target jobs -t beryl3-jobs:$VERSION_TAG -t beryl3-jobs:latest .
docker tag beryl3-jobs:$VERSION_TAG $REGISTRY/beryl3-jobs:$VERSION_TAG
docker tag beryl3-jobs:latest $REGISTRY/beryl3-jobs:latest

echo "Build completed successfully!"
echo "Version: $VERSION_TAG"
echo ""
echo "Local images tagged:"
echo "  beryl3-webapp:$VERSION_TAG"
echo "  beryl3-webapp:latest"
echo "  beryl3-jobs:$VERSION_TAG"
echo "  beryl3-jobs:latest"
echo ""
echo "Registry images tagged:"
echo "  $REGISTRY/beryl3-webapp:$VERSION_TAG"
echo "  $REGISTRY/beryl3-webapp:latest"
echo "  $REGISTRY/beryl3-jobs:$VERSION_TAG"
echo "  $REGISTRY/beryl3-jobs:latest"
echo ""
echo "To push images to registry, run: ./workflows/bin/push-to-gar.sh"