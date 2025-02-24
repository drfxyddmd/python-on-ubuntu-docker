#!/bin/bash
set -ex

echo "=== Generic Docker Image Hardening Workflow ==="

# Prompt for the image input in the format name:tag (e.g., mariadb:latest)
read -p "Enter image (format name:tag, e.g., mariadb:latest): " IMAGE

# Split the input into name and tag
NAME=$(echo "$IMAGE" | cut -d: -f1)
TAG=$(echo "$IMAGE" | cut -d: -f2)

# Pull the specified image from Docker Hub
echo "Pulling image $IMAGE..."
docker pull "$IMAGE"

# Generate the stub image using rfstub.
# This creates a new image tagged as ${NAME}:${TAG}-rfstub.
echo "Generating stub image from $IMAGE..."
rfstub "$IMAGE"
STUB_IMAGE="${NAME}:${TAG}-rfstub"

# Run the stub container with the SYS_PTRACE capability.
# The container is run in detached mode with port mapping 9999:80.
echo "Running stub container from $STUB_IMAGE..."
docker run --rm -d -p9999:80 --cap-add=SYS_PTRACE --name rf-test "$STUB_IMAGE"

# Wait a few seconds for the container to initialize.
echo "Waiting for container initialization..."
sleep 15

# Stop the running container.
echo "Stopping stub container..."
docker stop rf-test

# Harden the stub image using rfharden with preset "light".
# This creates a hardened image tagged as ${NAME}:${TAG}-rfhardened.
echo "Hardening stub image with preset 'light'..."
rfharden "$STUB_IMAGE" --preset light
HARDENED_IMAGE="${NAME}:${TAG}-rfhardened"

# Push the hardened image back to Docker Hub.
echo "Pushing hardened image $HARDENED_IMAGE..."
docker push "$HARDENED_IMAGE"

echo "Workflow completed successfully!"








name: Harden Docker Image

on:
  workflow_dispatch:
    inputs:
      registry:
        description: 'Docker registry (e.g., docker.io, ghcr.io, quay.io)'
        required: true
        default: 'docker.io'
      image_name:
        description: 'Image name (e.g., my-org/my-image or simply mariadb)'
        required: true
      preset:
        description: 'Hardening preset (light, medium, or hard)'
        required: true
        default: 'light'
        type: choice
        options:
          - light
          - medium
          - hard

jobs:
  harden:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v2

      - name: Login to Registry
        # Ensure you have set up the following secrets:
        # REGISTRY_USERNAME and REGISTRY_PASSWORD.
        run: |
          echo "${{ secrets.REGISTRY_PASSWORD }}" | docker login ${{ inputs.registry }} -u ${{ secrets.REGISTRY_USERNAME }} --password-stdin

      - name: Pull Original Image
        run: |
          echo "Pulling ${{ inputs.registry }}/${{ inputs.image_name }}:latest..."
          docker pull ${{ inputs.registry }}/${{ inputs.image_name }}:latest

      - name: Create Stub Image with rfstub
        run: |
          echo "Creating stub image..."
          rfstub ${{ inputs.registry }}/${{ inputs.image_name }}:latest
          # Assume the stub image gets tagged as <image_name>:latest-rfstub
          docker images

      - name: Run Stub Container
        run: |
          echo "Running stub container..."
          docker run --rm -d -p9999:80 --cap-add=SYS_PTRACE --name=rf-test ${{ inputs.registry }}/${{ inputs.image_name }}:latest-rfstub
          echo "Waiting for container initialization..."
          sleep 10
          echo "Stopping stub container..."
          docker stop rf-test

      - name: Harden Stub Image
        run: |
          echo "Hardening stub image with preset '${{ inputs.preset }}'..."
          rfharden ${{ inputs.registry }}/${{ inputs.image_name }}:latest-rfstub --preset ${{ inputs.preset }}
          # Assume the hardened image gets tagged as <image_name>:latest-rfhardened

      - name: Push Hardened Image
        run: |
          echo "Pushing hardened image to registry..."
          docker push ${{ inputs.registry }}/${{ inputs.image_name }}:latest-rfhardened









