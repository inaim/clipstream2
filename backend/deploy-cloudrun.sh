#!/usr/bin/env bash
set -euo pipefail

# Simple helper to build and deploy the backend to Cloud Run from local machine.
# Requires: gcloud (authenticated), docker (if building locally)

PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")
if [ -z "$PROJECT_ID" ]; then
  echo "gcloud project not set. Run: gcloud config set project YOUR_PROJECT_ID"
  exit 1
fi

REGION=${REGION:-us-central1}
SERVICE_NAME=${SERVICE_NAME:-clipstream-backend}
IMAGE=gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest

echo "Building Docker image: $IMAGE"
# Build multi-arch/amd64 image so Cloud Run (which expects linux/amd64) can run it
echo "Building and pushing Docker image for linux/amd64: $IMAGE"
if docker buildx ls >/dev/null 2>&1; then
  docker buildx build --platform linux/amd64 -t "$IMAGE" --push .
else
  echo "Warning: docker buildx not available; falling back to normal docker build. If you're on Apple Silicon (M1/M2) this may create an arm64 image that Cloud Run cannot run."
  docker build -t "$IMAGE" .
  docker push "$IMAGE"
fi

echo "Deploying to Cloud Run: $SERVICE_NAME in $REGION"
gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  # Do NOT set PORT - Cloud Run sets the PORT env var automatically.
  # Use --set-env-vars for other env vars here, for example:
  # --set-env-vars SURREALDB_URL=...,OTHER_VAR=...

echo "Deployment complete"
