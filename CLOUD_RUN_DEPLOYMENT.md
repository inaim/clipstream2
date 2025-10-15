# 🚀 ClipStream Cloud Run Deployment Guide

Complete guide to deploy ClipStream backend to Google Cloud Run and frontend to Cloud Storage/CDN.

## 📋 Prerequisites

1. **Google Cloud Account** with billing enabled
2. **gcloud CLI** installed and configured
3. **Docker** installed locally
4. **SurrealDB Cloud** account (already configured)
5. **Redis** instance (Upstash or Google Memorystore)

## 🏗️ Architecture

```
Frontend (Cloud Storage + CDN)
    ↓
Backend (Cloud Run)
    ↓
SurrealDB Cloud (AWS EU)
    ↓
Redis (Upstash/Memorystore)
```

---

## 🔧 Part 1: Backend Deployment to Cloud Run

### Step 1: Setup Google Cloud Project

```bash
# Set your project ID
export PROJECT_ID="clipstream-prod"
export REGION="europe-west1"  # Close to SurrealDB (AWS EU)

# Create project (if needed)
gcloud projects create $PROJECT_ID

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
    run.googleapis.com \
    containerregistry.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com
```

### Step 2: Configure Secrets

```bash
# Create secrets for sensitive data
echo -n "your-surrealdb-password" | gcloud secrets create surrealdb-password --data-file=-
echo -n "your-secret-key-min-32-chars" | gcloud secrets create app-secret-key --data-file=-
echo -n "your-google-oauth-client-id" | gcloud secrets create google-client-id --data-file=-
echo -n "your-google-oauth-secret" | gcloud secrets create google-client-secret --data-file=-

# Grant Cloud Run access to secrets
gcloud secrets add-iam-policy-binding surrealdb-password \
    --member="serviceAccount:${PROJECT_ID}@appspot.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### Step 3: Build and Push Docker Image

```bash
cd backend

# Build the image
gcloud builds submit --tag gcr.io/$PROJECT_ID/clipstream-backend \
    --dockerfile=Dockerfile.cloudrun

# Or build locally and push
docker build -t gcr.io/$PROJECT_ID/clipstream-backend -f Dockerfile.cloudrun .
docker push gcr.io/$PROJECT_ID/clipstream-backend
```

### Step 4: Deploy to Cloud Run

```bash
gcloud run deploy clipstream-backend \
    --image gcr.io/$PROJECT_ID/clipstream-backend \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --concurrency 80 \
    --min-instances 0 \
    --max-instances 10 \
    --set-env-vars="APP_ENV=production" \
    --set-env-vars="SURREALDB_URL=wss://ancient-valley-06cu6ilhgptbp4ttr1a04b77oc.aws-euw1.surreal.cloud" \
    --set-env-vars="SURREALDB_USER=root" \
    --set-env-vars="SURREALDB_NS=clipstream" \
    --set-env-vars="SURREALDB_DB=production" \
    --set-env-vars="BACKEND_BASE_URL=https://backend.finailabz.com" \
    --set-env-vars="FRONTEND_BASE_URL=https://clipstream.finailabz.com" \
    --set-env-vars="ALLOWED_ORIGINS=[\"https://clipstream.finailabz.com\"]" \
    --set-secrets="SURREALDB_PASS=surrealdb-password:latest" \
    --set-secrets="SECRET_KEY=app-secret-key:latest" \
    --set-secrets="GOOGLE_CLIENT_ID=google-client-id:latest" \
    --set-secrets="GOOGLE_CLIENT_SECRET=google-client-secret:latest"
```

### Step 5: Configure Custom Domain

```bash
# Map custom domain
gcloud run domain-mappings create \
    --service clipstream-backend \
    --domain backend.finailabz.com \
    --region $REGION

# Get the DNS records to configure
gcloud run domain-mappings describe \
    --domain backend.finailabz.com \
    --region $REGION
```

**Add these DNS records to your domain:**
- Type: `A` or `CNAME`
- Name: `backend`
- Value: (from command output)

---

## 🌐 Part 2: Frontend Deployment to Cloud Storage + CDN

### Step 1: Build Frontend

```bash
cd frontend

# Install dependencies
npm install

# Build for production
VITE_API_BASE_URL=https://backend.finailabz.com \
VITE_BACKEND_URL=https://backend.finailabz.com \
npm run build
```

### Step 2: Create Cloud Storage Bucket

```bash
# Create bucket
gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://clipstream-frontend

# Make bucket public
gsutil iam ch allUsers:objectViewer gs://clipstream-frontend

# Configure as website
gsutil web set -m index.html -e index.html gs://clipstream-frontend

# Enable CORS
cat > cors.json <<EOF
[
  {
    "origin": ["*"],
    "method": ["GET", "HEAD"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600
  }
]
EOF

gsutil cors set cors.json gs://clipstream-frontend
```

### Step 3: Upload Frontend

```bash
# Upload build files
gsutil -m rsync -r -d dist/ gs://clipstream-frontend/

# Set cache control
gsutil -m setmeta -h "Cache-Control:public, max-age=31536000" \
    gs://clipstream-frontend/assets/**

gsutil -m setmeta -h "Cache-Control:public, max-age=3600" \
    gs://clipstream-frontend/index.html
```

### Step 4: Setup Cloud CDN (Optional but Recommended)

```bash
# Create backend bucket
gcloud compute backend-buckets create clipstream-frontend-backend \
    --gcs-bucket-name=clipstream-frontend \
    --enable-cdn

# Create URL map
gcloud compute url-maps create clipstream-frontend-url-map \
    --default-backend-bucket=clipstream-frontend-backend

# Create SSL certificate
gcloud compute ssl-certificates create clipstream-frontend-cert \
    --domains=clipstream.finailabz.com

# Create target HTTPS proxy
gcloud compute target-https-proxies create clipstream-frontend-proxy \
    --url-map=clipstream-frontend-url-map \
    --ssl-certificates=clipstream-frontend-cert

# Create forwarding rule
gcloud compute forwarding-rules create clipstream-frontend-https \
    --global \
    --target-https-proxy=clipstream-frontend-proxy \
    --ports=443

# Get the IP address
gcloud compute forwarding-rules describe clipstream-frontend-https --global
```

**Add DNS record:**
- Type: `A`
- Name: `@` or `clipstream`
- Value: (IP from command output)

---

## 🔐 Part 3: Environment Variables

### Backend Environment Variables (Cloud Run)

Set these via Cloud Run console or `gcloud run services update`:

```bash
# Required
SURREALDB_URL=wss://ancient-valley-06cu6ilhgptbp4ttr1a04b77oc.aws-euw1.surreal.cloud
SURREALDB_USER=root
SURREALDB_PASS=<secret>
SURREALDB_NS=clipstream
SURREALDB_DB=production

# Application
APP_ENV=production
SECRET_KEY=<secret>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# URLs
BACKEND_BASE_URL=https://backend.finailabz.com
FRONTEND_BASE_URL=https://clipstream.finailabz.com
ALLOWED_ORIGINS=["https://clipstream.finailabz.com"]

# OAuth
GOOGLE_CLIENT_ID=<secret>
GOOGLE_CLIENT_SECRET=<secret>

# Optional
REDIS_URL=redis://your-redis-host:6379/0
ENABLE_IPFS=false
```

### Frontend Environment Variables (Build Time)

Set these in `.env.production` or build command:

```bash
VITE_API_BASE_URL=https://backend.finailabz.com
VITE_BACKEND_URL=https://backend.finailabz.com
```

---

## 📊 Part 4: Monitoring & Logging

### Enable Logging

```bash
# View logs
gcloud run services logs read clipstream-backend \
    --region $REGION \
    --limit 50

# Stream logs
gcloud run services logs tail clipstream-backend \
    --region $REGION
```

### Setup Monitoring

```bash
# Create uptime check
gcloud monitoring uptime create clipstream-backend-health \
    --resource-type=uptime-url \
    --host=backend.finailabz.com \
    --path=/health \
    --period=60

# Create alert policy
gcloud alpha monitoring policies create \
    --notification-channels=YOUR_CHANNEL_ID \
    --display-name="ClipStream Backend Down" \
    --condition-display-name="Health Check Failed" \
    --condition-threshold-value=1 \
    --condition-threshold-duration=300s
```

---

## 🔄 Part 5: CI/CD with GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]

env:
  PROJECT_ID: clipstream-prod
  REGION: europe-west1
  SERVICE_NAME: clipstream-backend

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: ${{ env.PROJECT_ID }}
      
      - name: Build and Push
        run: |
          gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME \
            --dockerfile=backend/Dockerfile.cloudrun backend/
      
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy $SERVICE_NAME \
            --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
            --region $REGION \
            --platform managed

  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Build Frontend
        run: |
          cd frontend
          npm ci
          VITE_API_BASE_URL=https://backend.finailabz.com npm run build
      
      - name: Deploy to Cloud Storage
        uses: google-github-actions/upload-cloud-storage@v1
        with:
          path: frontend/dist
          destination: clipstream-frontend
          parent: false
```

---

## 💰 Cost Estimation

### Cloud Run (Backend)
- **Free tier**: 2 million requests/month
- **After free tier**: ~$0.40 per million requests
- **Estimated**: $10-50/month (depending on traffic)

### Cloud Storage (Frontend)
- **Storage**: $0.020 per GB/month
- **Bandwidth**: $0.12 per GB (first 1TB)
- **Estimated**: $5-20/month

### Cloud CDN (Optional)
- **Cache fill**: $0.08 per GB
- **Cache hit**: $0.04 per GB
- **Estimated**: $10-30/month

### SurrealDB Cloud
- **Your current plan**: Check SurrealDB pricing

### Total Estimated Cost
- **Minimum**: $25-50/month
- **With moderate traffic**: $50-150/month

---

## ✅ Deployment Checklist

### Pre-Deployment
- [ ] SurrealDB Cloud configured and accessible
- [ ] Google Cloud project created
- [ ] Domain DNS configured
- [ ] OAuth credentials obtained
- [ ] Environment variables prepared

### Backend Deployment
- [ ] Docker image built and pushed
- [ ] Cloud Run service deployed
- [ ] Custom domain mapped
- [ ] Secrets configured
- [ ] Health check passing

### Frontend Deployment
- [ ] Frontend built with production API URL
- [ ] Cloud Storage bucket created
- [ ] Files uploaded
- [ ] CDN configured (optional)
- [ ] Custom domain configured

### Post-Deployment
- [ ] Test authentication flow
- [ ] Test video upload
- [ ] Test API endpoints
- [ ] Configure monitoring
- [ ] Setup alerts
- [ ] Enable logging

---

## 🐛 Troubleshooting

### Backend Issues

**Service won't start:**
```bash
# Check logs
gcloud run services logs read clipstream-backend --region $REGION --limit 100

# Check environment variables
gcloud run services describe clipstream-backend --region $REGION
```

**Database connection fails:**
- Verify SurrealDB URL is correct
- Check SurrealDB credentials
- Ensure Cloud Run has internet access

**CORS errors:**
- Verify ALLOWED_ORIGINS includes frontend URL
- Check CORS middleware configuration

### Frontend Issues

**API calls fail:**
- Verify VITE_API_BASE_URL is correct
- Check backend CORS configuration
- Verify backend is accessible

**Assets not loading:**
- Check Cloud Storage bucket permissions
- Verify cache control headers
- Check CDN configuration

---

## 🚀 Quick Deploy Commands

### Deploy Backend
```bash
cd backend
gcloud run deploy clipstream-backend \
    --source . \
    --region europe-west1 \
    --allow-unauthenticated
```

### Deploy Frontend
```bash
cd frontend
npm run build
gsutil -m rsync -r -d dist/ gs://clipstream-frontend/
```

---

## 📚 Additional Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Storage Documentation](https://cloud.google.com/storage/docs)
- [Cloud CDN Documentation](https://cloud.google.com/cdn/docs)
- [SurrealDB Cloud](https://surrealdb.com/cloud)

---

**Your backend is now ready for Cloud Run deployment! 🎉**

