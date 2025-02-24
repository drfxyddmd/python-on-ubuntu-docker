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










name: Generic Docker Image Hardening Demo

on:
  schedule:
    - cron: '0 5 * * *'
  workflow_dispatch:
    inputs:
      image:
        description: 'Enter image in format name:tag (e.g., mariadb:latest)'
        required: true
        default: 'mariadb:latest'

permissions: read-all

jobs:
  build:
    runs-on: ubuntu-latest
    environment: actions-cicd
    steps:
      - name: Install RapidFort CLI Tools
        run: curl https://frontrow.rapidfort.com/cli/ | bash

      - name: Authenticate with RapidFort
        env:
          RF_ACCESS_ID: ${{ secrets.RF_ACCESS_ID }}
          RF_SECRET_ACCESS_KEY: ${{ secrets.RF_SECRET_ACCESS_KEY }}
        run: rflogin

      - name: Pull the input image
        run: |
          echo "Pulling image ${{ inputs.image }}..."
          docker pull ${{ inputs.image }}

      - name: Generate Stub Image with rfstub
        run: |
          echo "Generating stub image from ${{ inputs.image }}..."
          rfstub ${{ inputs.image }}
          # Extract name and tag from the input
          NAME=$(echo "${{ inputs.image }}" | cut -d: -f1)
          TAG=$(echo "${{ inputs.image }}" | cut -d: -f2)
          STUB_IMAGE="${NAME}:${TAG}-rfstub"
          echo "Stub image created: $STUB_IMAGE"
          docker images | grep "$NAME"

      - name: Run Stub Container
        run: |
          # Compute stub image name
          NAME=$(echo "${{ inputs.image }}" | cut -d: -f1)
          TAG=$(echo "${{ inputs.image }}" | cut -d: -f2)
          STUB_IMAGE="${NAME}:${TAG}-rfstub"
          echo "Running container from stub image $STUB_IMAGE..."
          docker run --rm -d -p9999:80 --cap-add=SYS_PTRACE --name rf-test "$STUB_IMAGE"
          echo "Waiting for container initialization..."
          sleep 15
          echo "Stopping container..."
          docker stop rf-test

      - name: Harden Stub Image with rfharden
        run: |
          # Recompute stub image name
          NAME=$(echo "${{ inputs.image }}" | cut -d: -f1)
          TAG=$(echo "${{ inputs.image }}" | cut -d: -f2)
          STUB_IMAGE="${NAME}:${TAG}-rfstub"
          echo "Hardening stub image $STUB_IMAGE with preset 'light'..."
          rfharden "$STUB_IMAGE" --preset light

      - name: Push Hardened Image
        run: |
          # Compute hardened image name (assumes tag is appended with '-rfhardened')
          NAME=$(echo "${{ inputs.image }}" | cut -d: -f1)
          TAG=$(echo "${{ inputs.image }}" | cut -d: -f2)
          HARDENED_IMAGE="${NAME}:${TAG}-rfhardened"
          echo "Pushing hardened image $HARDENED_IMAGE..."
          docker push "$HARDENED_IMAGE"

      - name: Complete
        run: echo "For more information, please visit: https://docs.rapidfort.com/getting-started/docker"








