#!/bin/bash
# Build and push test-runner image for faster CI/CD
# Run this ONCE after updating requirements.txt

set -e

IMAGE="europe-central2-docker.pkg.dev/gen-lang-client-0508446677/sight-containers/test-runner:latest"

echo "🏗️  Building test-runner image..."
docker build -f Dockerfile.test -t "$IMAGE" .

echo "📤 Pushing to Artifact Registry..."
docker push "$IMAGE"

echo "✅ Test runner image ready!"
echo "   Image: $IMAGE"
echo ""
echo "Next builds will use this cached image (5 min → <60s)"
