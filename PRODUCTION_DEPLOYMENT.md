# ClipStream Production Deployment Guide

This guide covers deploying ClipStream to production environments.

---

## 🚀 Quick Deploy Options

### Option 1: Vercel + Railway (Recommended for MVP)

**Frontend (Vercel):**
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy frontend
cd frontend
vercel --prod
```

**Backend (Railway):**
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

**Estimated Cost:** $20-50/month

---

### Option 2: Docker Compose (VPS)

**Requirements:**
- VPS with 4GB+ RAM (DigitalOcean, Linode, Vultr)
- Docker & Docker Compose installed
- Domain name with DNS configured

**Steps:**

```bash
# 1. Clone repository
git clone https://github.com/yourusername/clipstream.git
cd clipstream

# 2. Configure environment
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
# Edit .env files with production values

# 3. Build and start services
docker-compose -f docker-compose.prod.yml up -d

# 4. Setup SSL with Let's Encrypt
docker-compose exec nginx certbot --nginx -d yourdomain.com
```

**Estimated Cost:** $20-40/month

---

### Option 3: Kubernetes (Scalable Production)

**Requirements:**
- Kubernetes cluster (GKE, EKS, AKS, or DigitalOcean Kubernetes)
- kubectl configured
- Helm installed

**Steps:**

```bash
# 1. Create namespace
kubectl create namespace clipstream

# 2. Deploy with Helm
helm install clipstream ./k8s/helm \
  --namespace clipstream \
  --set backend.replicas=3 \
  --set celery.replicas=4

# 3. Configure ingress
kubectl apply -f k8s/ingress.yaml

# 4. Setup monitoring
helm install prometheus prometheus-community/kube-prometheus-stack
```

**Estimated Cost:** $100-500/month

---

## 🔧 Environment Configuration

### Frontend Environment Variables

```env
# Production .env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-production-anon-key
VITE_BACKEND_URL=https://api.yourdomain.com
VITE_IPFS_GATEWAY=https://ipfs.yourdomain.com
VITE_ENV=production
```

### Backend Environment Variables

```env
# Production .env
APP_ENV=production
DEBUG=False
SECRET_KEY=your-super-secret-key-min-32-chars
ALLOWED_HOSTS=api.yourdomain.com,yourdomain.com

# Database
SURREALDB_URL=https://your-surrealdb-cloud.com
SURREALDB_USER=admin
SURREALDB_PASS=strong-password

# Redis
REDIS_URL=redis://your-redis-cloud.com:6379/0

# IPFS
IPFS_API_URL=https://ipfs-api.yourdomain.com
IPFS_GATEWAY_URL=https://ipfs.yourdomain.com

# Blockchain
POLYGON_RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/YOUR-KEY
WATCH_TOKEN_ADDRESS=0xYourDeployedTokenAddress
PRIVATE_KEY=your-wallet-private-key

# AI Services
OPENAI_API_KEY=sk-your-openai-key

# Email
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
```

---

## 📦 Database Setup

### SurrealDB Cloud

```bash
# 1. Sign up at https://surrealdb.com/cloud

# 2. Create database instance
# - Region: Choose closest to your users
# - Plan: Start with Standard ($29/month)

# 3. Initialize schema
surreal import \
  --conn https://your-instance.surrealdb.cloud \
  --user root \
  --pass your-password \
  --ns clipstream \
  --db main \
  ./scripts/schema.surql
```

### Redis Cloud

```bash
# 1. Sign up at https://redis.com/cloud

# 2. Create database
# - Cloud: AWS/GCP/Azure
# - Region: Same as your backend
# - Plan: 1GB cache ($10/month)

# 3. Get connection URL
# Format: redis://default:password@host:port
```

---

## 🎬 IPFS Setup

### Option 1: Pinata (Managed IPFS)

```bash
# 1. Sign up at https://pinata.cloud

# 2. Get API keys
# - JWT token for authentication

# 3. Configure backend
IPFS_PINNING_SERVICE=pinata
PINATA_JWT=your-jwt-token
```

### Option 2: Web3.Storage

```bash
# 1. Sign up at https://web3.storage

# 2. Create API token

# 3. Configure backend
IPFS_PINNING_SERVICE=web3storage
WEB3_STORAGE_TOKEN=your-token
```

### Option 3: Self-Hosted IPFS

```bash
# Run IPFS node
docker run -d \
  --name ipfs \
  -p 4001:4001 \
  -p 5001:5001 \
  -p 8080:8080 \
  -v /data/ipfs:/data/ipfs \
  ipfs/kubo:latest
```

---

## 🔐 SSL/TLS Setup

### Let's Encrypt (Free)

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal (cron job)
0 0 * * * certbot renew --quiet
```

### Cloudflare (Recommended)

```bash
# 1. Add domain to Cloudflare
# 2. Update nameservers
# 3. Enable "Full (strict)" SSL mode
# 4. Enable "Always Use HTTPS"
# 5. Enable "Automatic HTTPS Rewrites"
```

---

## 📊 Monitoring Setup

### Sentry (Error Tracking)

```bash
# 1. Sign up at https://sentry.io

# 2. Create project
# - Platform: Python (backend)
# - Platform: React (frontend)

# 3. Install SDK
pip install sentry-sdk
npm install @sentry/react

# 4. Initialize
# Backend
import sentry_sdk
sentry_sdk.init(dsn="your-dsn")

# Frontend
import * as Sentry from "@sentry/react";
Sentry.init({ dsn: "your-dsn" });
```

### Prometheus + Grafana

```bash
# Deploy with Docker Compose
docker-compose -f monitoring/docker-compose.yml up -d

# Access Grafana
# URL: http://your-server:3000
# Default: admin/admin

# Import dashboards
# - FastAPI metrics
# - Celery metrics
# - Redis metrics
# - System metrics
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest

  deploy-frontend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.ORG_ID }}
          vercel-project-id: ${{ secrets.PROJECT_ID }}
          vercel-args: '--prod'

  deploy-backend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Railway
        uses: bervProject/railway-deploy@main
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN }}
          service: backend
```

---

## 🧪 Pre-Deployment Checklist

### Security

- [ ] Change all default passwords
- [ ] Generate strong SECRET_KEY (32+ characters)
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Enable firewall rules
- [ ] Rotate API keys regularly
- [ ] Set up backup encryption

### Performance

- [ ] Enable Redis caching
- [ ] Configure CDN (Cloudflare)
- [ ] Optimize database indexes
- [ ] Enable gzip compression
- [ ] Set up image optimization
- [ ] Configure video CDN
- [ ] Enable browser caching

### Monitoring

- [ ] Set up error tracking (Sentry)
- [ ] Configure uptime monitoring
- [ ] Set up log aggregation
- [ ] Enable performance monitoring
- [ ] Configure alerts
- [ ] Set up backup monitoring

### Compliance

- [ ] Add Privacy Policy
- [ ] Add Terms of Service
- [ ] Configure GDPR compliance
- [ ] Set up data retention policy
- [ ] Enable audit logging
- [ ] Configure content moderation

---

**Deployment completed! 🎉**

Your ClipStream instance should now be live and ready to handle users!

