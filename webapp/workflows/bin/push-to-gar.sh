#!/bin/bash
set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration
VERSION_FILE="$PROJECT_ROOT/VERSION"
REGISTRY="europe-west6-docker.pkg.dev/beryl3/beryl3"

echo "Pushing Docker images to Google Artifact Registry..."
echo "Project root: $PROJECT_ROOT"

# Change to project root
cd "$PROJECT_ROOT"

# Check if VERSION file exists
if [ ! -f "$VERSION_FILE" ]; then
    echo "ERROR: VERSION file not found. Run ./workflows/bin/image-build.sh first."
    exit 1
fi

# Source the version file
source $VERSION_FILE
VERSION_TAG="$MAJOR.$MINOR.$BUILD"

echo "Pushing version: $VERSION_TAG"

# Check if images exist locally
if ! docker image inspect beryl3-webapp:$VERSION_TAG >/dev/null 2>&1; then
    echo "ERROR: Local image beryl3-webapp:$VERSION_TAG not found. Run ./workflows/bin/image-build.sh first."
    exit 1
fi

if ! docker image inspect beryl3-jobs:$VERSION_TAG >/dev/null 2>&1; then
    echo "ERROR: Local image beryl3-jobs:$VERSION_TAG not found. Run ./workflows/bin/image-build.sh first."
    exit 1
fi

# Configure Docker authentication (if not already done)
echo "Configuring Docker authentication for GAR..."
/home/mdubiel/google-cloud-sdk/bin/gcloud auth configure-docker europe-west6-docker.pkg.dev --quiet

# Push webapp images
echo "Pushing webapp images..."
docker push $REGISTRY/beryl3-webapp:$VERSION_TAG
docker push $REGISTRY/beryl3-webapp:latest

# Push jobs images
echo "Pushing jobs images..."
docker push $REGISTRY/beryl3-jobs:$VERSION_TAG
docker push $REGISTRY/beryl3-jobs:latest

echo "Push completed successfully!"
echo ""
echo "Pushed images:"
echo "  $REGISTRY/beryl3-webapp:$VERSION_TAG"
echo "  $REGISTRY/beryl3-webapp:latest"
echo "  $REGISTRY/beryl3-jobs:$VERSION_TAG"
echo "  $REGISTRY/beryl3-jobs:latest"
echo ""
echo "Images are now available in Google Artifact Registry"
echo "To deploy with new images, run:"
echo "  ./workflows/bin/deploy-qa-webapp.sh    # Deploy webapp"
echo "  ./workflows/bin/deploy-qa-jobs.sh      # Deploy jobs"