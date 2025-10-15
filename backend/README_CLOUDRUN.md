# Deploying ClipStream Backend to Google Cloud Run

This file documents quick steps to build and deploy the backend to Cloud Run.

Prerequisites
- Google Cloud SDK (gcloud) installed and authenticated
- Docker installed (for local builds)
- A Google Cloud project with billing enabled

Quick local deploy (build, push, deploy)

1. Set your project:

```bash
gcloud config set project YOUR_PROJECT_ID
```

2. Build & deploy locally using the provided helper script (from `backend/`):

```bash
cd backend
./deploy-cloudrun.sh
```

This script builds the image, pushes it to `gcr.io/$PROJECT_ID/clipstream-backend:latest`, and deploys to Cloud Run.

Using Cloud Build (CI/CD)

You can also use the included `cloudbuild.yaml` which will build, push and deploy via Cloud Build. Submit a build like:

```bash
gcloud builds submit --config cloudbuild.yaml --substitutions=_REGION=us-central1,_SERVICE_NAME=clipstream-backend
```

Notes & production recommendations
- Use Cloud Storage for uploaded files. The container filesystem is ephemeral; Cloud Run instances only have writable `/tmp` which is not persistent between instances. Implement signed URL uploads to GCS or proxy uploads to GCS from the backend.
- Use Secret Manager to store SURREALDB credentials and set them in Cloud Run using `--set-secrets` or via the Cloud Console.
- If you see apt errors in Docker builds (earlier observed HTTP 400 from apt archive), switch to `Dockerfile.cloudrun` which uses a builder stage and keeps runtime image minimal; also consider using a Debian mirror or retrying later.

Helpful environment variables
- PORT (Cloud Run sets this automatically to the container port, default 8080)
- SURREALDB_URL, SURREALDB_USER, SURREALDB_PASS, SURREALDB_NS, SURREALDB_DB (use Secret Manager)
