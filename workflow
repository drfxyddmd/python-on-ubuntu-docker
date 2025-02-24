#!/bin/bash
set -e

echo "=== Local Docker Image Hardening Workflow ==="

# Prompt for user inputs
read -p "Enter the registry (e.g., docker.io): " REGISTRY
read -p "Enter the image name (e.g., mariadb): " IMAGE_NAME
read -p "Enter the hardening preset (light, medium, or hard): " PRESET

# Construct full image names
ORIGINAL_IMAGE="${REGISTRY}/${IMAGE_NAME}:latest"
STUB_IMAGE="${IMAGE_NAME}:latest-rfstub"
HARDENED_IMAGE="${REGISTRY}/${IMAGE_NAME}:latest-rfhardened"

echo "Pulling original image: ${ORIGINAL_IMAGE}..."
docker pull "${ORIGINAL_IMAGE}"

echo "Creating stub image using rfstub..."
rfstub "${ORIGINAL_IMAGE}"
# The stub image is expected to be tagged as ${STUB_IMAGE}
docker images | grep "${IMAGE_NAME}"

echo "Running stub container..."
docker run --rm -d -p9999:80 --cap-add=SYS_PTRACE --name rf-test "${STUB_IMAGE}"
echo "Waiting for container initialization..."
sleep 10
echo "Stopping stub container..."
docker stop rf-test

echo "Hardening stub image with preset '${PRESET}'..."
rfharden "${STUB_IMAGE}" --preset "${PRESET}"
# The hardened image is expected to be tagged as ${HARDENED_IMAGE}

echo "Pushing hardened image: ${HARDENED_IMAGE}..."
docker push "${HARDENED_IMAGE}"

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









