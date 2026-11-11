#!/bin/bash
# Build script for the omicairn-claude-code Docker image
# Usage: ./build-image.sh [version]
# Example: ./build-image.sh v1.0.0
#
# By default the image is only built locally. To also push it to your own
# container registry, set REGISTRY (e.g. <YOUR_REGISTRY>/<namespace>) and PUSH=1.
# Registry login is left to you (e.g. `docker login`, `aws ecr get-login-password ...`).

set -e

# Default version if not provided
if [ -z "$1" ]; then
    echo "Please input the version of the image:"
    read version
else
    version=$1
fi

IMAGE_NAME="${IMAGE_NAME:-omicairn-claude-code}"
PLATFORM="${PLATFORM:-linux/amd64}"
if [ -n "${REGISTRY}" ]; then
    FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}"
else
    FULL_IMAGE_NAME="${IMAGE_NAME}"
fi

echo "=== Building omicairn-claude-code Docker image ==="
echo "Version: ${version}"
echo "Image: ${FULL_IMAGE_NAME}"
echo ""

echo "Building Docker image for ${PLATFORM}..."
docker build --platform "${PLATFORM}" -t "${FULL_IMAGE_NAME}:${version}" .
docker tag "${FULL_IMAGE_NAME}:${version}" "${FULL_IMAGE_NAME}:latest"

if [ "${PUSH:-0}" = "1" ]; then
    if [ -z "${REGISTRY}" ]; then
        echo "PUSH=1 requires REGISTRY to be set" >&2
        exit 1
    fi
    echo ""
    echo "Pushing Docker image..."
    docker push "${FULL_IMAGE_NAME}:${version}"
    docker push "${FULL_IMAGE_NAME}:latest"
fi

echo ""
echo "=== Build complete ==="
echo "Image: ${FULL_IMAGE_NAME}:${version} (and :latest)"
