# PRODUCTION DEPLOYMENT GUIDE

## Overview
This guide covers deploying AI Judge to production with proper scalability, security, and monitoring.

---

## Prerequisites

### Required Accounts
- [ ] Groq API account (https://console.groq.com/)
- [ ] GitHub account
- [ ] Vercel account (for frontend)
- [ ] Railway/Render account (for backend)
- [ ] (Optional) AWS/GCP/Azure account

### Required Tools
- [ ] Git
- [ ] Docker & Docker Compose
- [ ] kubectl (for Kubernetes)
- [ ] Terraform (for IaC)

---

## Deployment Options

### Option 1: Quick Deploy (Free Tier) ⚡

#### Frontend: Vercel
```bash
# 1. Push to GitHub
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/ai-judge.git
git push -u origin main

# 2. Import to Vercel
# - Go to vercel.com
# - Import Git Repository
# - Select your repo
# - Set Root Directory: frontend
# - Add environment variable:
#   NEXT_PUBLIC_API_URL = https://your-backend-url.com

# 3. Deploy
# Vercel auto-deploys on push
```

#### Backend: Railway
```bash
# 1. Install Railway CLI
npm i -g @railway/cli

# 2. Login
railway login

# 3. Initialize
cd backend
railway init

# 4. Add environment variables
railway variables set GROQ_API_KEY=your_key_here

# 5. Deploy
railway up

# 6. Get URL
railway status
```

**Total Cost:** $0/month (within free tier limits)

---

### Option 2: Docker Compose (VPS) 🐳

#### Prerequisites
- Ubuntu 22.04 VPS (DigitalOcean, Linode, etc.)
- Minimum 2GB RAM, 2 vCPUs

#### Setup
```bash
# 1. SSH into VPS
ssh root@your-server-ip

# 2. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 3. Install Docker Compose
apt install docker-compose -y

# 4. Clone repo
git clone https://github.com/yourusername/ai-judge.git
cd ai-judge

# 5. Create .env
cat > backend/.env << EOF
GROQ_API_KEY=your_key_here
EOF

# 6. Start services
docker-compose up -d

# 7. Setup Nginx reverse proxy
apt install nginx -y
cat > /etc/nginx/sites-available/ai-judge << 'EOF'
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
EOF

ln -s /etc/nginx/sites-available/ai-judge /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx

# 8. Setup SSL with Let's Encrypt
apt install certbot python3-certbot-nginx -y
certbot --nginx -d yourdomain.com
```

**Estimated Cost:** $5-10/month (VPS)

---

### Option 3: Kubernetes (Production Scale) ☸️

#### Prerequisites
- Kubernetes cluster (EKS, GKE, AKS, or self-hosted)
- kubectl configured
- Docker registry (ECR, GCR, Docker Hub)

#### Build & Push Images
```bash
# Backend
cd backend
docker build -t your-registry/ai-judge-backend:latest .
docker push your-registry/ai-judge-backend:latest

# Frontend
cd ../frontend
docker build -t your-registry/ai-judge-frontend:latest .
docker push your-registry/ai-judge-frontend:latest
```

#### Create Secrets
```bash
kubectl create namespace ai-judge

kubectl create secret generic ai-judge-secrets \
  --from-literal=groq-api-key=your_key_here \
  -n ai-judge
```

#### Deploy
```bash
# Apply configurations
kubectl apply -f k8s/deployment.yaml -n ai-judge

# Check status
kubectl get pods -n ai-judge
kubectl get services -n ai-judge

# Get external IP
kubectl get svc ai-judge-backend-service -n ai-judge
```

#### Auto-scaling Configuration
```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ai-judge-backend-hpa
  namespace: ai-judge
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-judge-backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**Estimated Cost:** $100-500/month (depending on scale)

---

## Database Setup (Production)

### PostgreSQL on AWS RDS
```bash
# 1. Create RDS instance
# - Engine: PostgreSQL 15
# - Instance: db.t3.medium
# - Storage: 100GB SSD
# - Multi-AZ: Yes (for high availability)

# 2. Create database
psql -h your-rds-endpoint -U postgres -c "CREATE DATABASE ai_judge;"

# 3. Run migrations
cd backend
alembic upgrade head
```

### Schema
```sql
CREATE TABLE cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id VARCHAR(255) UNIQUE NOT NULL,
    side_a_text TEXT,
    side_b_text TEXT,
    initial_verdict TEXT,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id VARCHAR(255) REFERENCES cases(case_id),
    side VARCHAR(1),
    filename VARCHAR(255),
    file_path TEXT,
    extracted_text TEXT,
    uploaded_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE follow_ups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id VARCHAR(255) REFERENCES cases(case_id),
    side VARCHAR(1),
    argument TEXT,
    response TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_cases_created_at ON cases(created_at);
CREATE INDEX idx_cases_status ON cases(status);
CREATE INDEX idx_documents_case_id ON documents(case_id);
CREATE INDEX idx_follow_ups_case_id ON follow_ups(case_id);
```

---

## Redis Setup (Caching)

### Redis Cloud (Free Tier)
```bash
# 1. Sign up at redis.com
# 2. Create free database
# 3. Get connection URL

# 4. Update backend code
# pip install redis
```

```python
# backend/cache.py
import redis
import json
from functools import wraps

redis_client = redis.from_url(os.environ.get("REDIS_URL"))

def cache_verdict(ttl=86400):  # 24 hours
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            cache_key = f"verdict:{hash(str(args))}"
            
            # Try to get from cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Generate verdict
            result = func(*args, **kwargs)
            
            # Cache result
            redis_client.setex(
                cache_key,
                ttl,
                json.dumps(result)
            )
            
            return result
        return wrapper
    return decorator
```

---

## Monitoring Setup

### Prometheus + Grafana
```yaml
# k8s/monitoring.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
      - job_name: 'ai-judge-backend'
        static_configs:
          - targets: ['ai-judge-backend-service:8000']
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:latest
        ports:
        - containerPort: 9090
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:latest
        ports:
        - containerPort: 3000
```

### Application Metrics (Backend)
```python
# backend/metrics.py
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Response

# Metrics
case_created_counter = Counter('cases_created_total', 'Total cases created')
verdict_duration = Histogram('verdict_generation_seconds', 'Verdict generation time')
llm_tokens_used = Counter('llm_tokens_used_total', 'Total LLM tokens used')

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Error Tracking: Sentry
```bash
# Install
pip install sentry-sdk

# Initialize
import sentry_sdk
sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=1.0
)
```

---

## CI/CD Pipeline

### GitHub Actions
```yaml
# .github/workflows/production.yml
name: Production Deploy

on:
  push:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run backend tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest
      
      - name: Run frontend tests
        run: |
          cd frontend
          npm install
          npm run test

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      
      - name: Build and push backend
        run: |
          docker build -t ${{ secrets.DOCKER_USERNAME }}/ai-judge-backend:${{ github.sha }} backend/
          docker push ${{ secrets.DOCKER_USERNAME }}/ai-judge-backend:${{ github.sha }}
      
      - name: Build and push frontend
        run: |
          docker build -t ${{ secrets.DOCKER_USERNAME }}/ai-judge-frontend:${{ github.sha }} frontend/
          docker push ${{ secrets.DOCKER_USERNAME }}/ai-judge-frontend:${{ github.sha }}

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/ai-judge-backend \
            backend=${{ secrets.DOCKER_USERNAME }}/ai-judge-backend:${{ github.sha }} \
            -n ai-judge
          
          kubectl set image deployment/ai-judge-frontend \
            frontend=${{ secrets.DOCKER_USERNAME }}/ai-judge-frontend:${{ github.sha }} \
            -n ai-judge
```

---

## Security Hardening

### 1. Environment Variables
```bash
# Never commit .env files
# Use secrets manager

# AWS Secrets Manager
aws secretsmanager create-secret \
  --name ai-judge/groq-api-key \
  --secret-string "your_key_here"
```

### 2. Rate Limiting
```python
# backend/middleware.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/case/create")
@limiter.limit("5/minute")
def create_case(request: Request, case: CaseCreate):
    # ... existing code
```

### 3. HTTPS Only
```python
# backend/app.py
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

if os.environ.get("ENVIRONMENT") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)
```

### 4. Input Validation
```python
from pydantic import BaseModel, Field, validator

class CaseCreate(BaseModel):
    case_id: str = Field(..., min_length=3, max_length=100)
    
    @validator('case_id')
    def case_id_valid(cls, v):
        if not v.isalnum():
            raise ValueError('case_id must be alphanumeric')
        return v
```

---

## Backup Strategy

### Database Backups
```bash
# Automated daily backups
crontab -e

# Add:
0 2 * * * pg_dump -h your-db-host -U postgres ai_judge | gzip > /backups/ai-judge-$(date +\%Y\%m\%d).sql.gz
```

### Document Storage Backups
```bash
# S3 versioning enabled
aws s3api put-bucket-versioning \
  --bucket ai-judge-documents \
  --versioning-configuration Status=Enabled

# Lifecycle policy
aws s3api put-bucket-lifecycle-configuration \
  --bucket ai-judge-documents \
  --lifecycle-configuration file://lifecycle.json
```

---

## Cost Estimation

### Small Scale (100 users/day)
- Vercel: $0 (free tier)
- Railway: $0 (free tier)
- Groq API: $0 (free tier)
- **Total: $0/month**

### Medium Scale (1,000 users/day)
- VPS: $20/month
- Database: $15/month
- Redis: $0 (free tier)
- CDN: $5/month
- Groq API: $0-50/month
- **Total: $40-90/month**

### Large Scale (10,000 users/day)
- Kubernetes: $150/month
- Database: $100/month
- Redis: $20/month
- CDN: $50/month
- Load Balancer: $20/month
- Monitoring: $30/month
- Groq API: $200-500/month
- **Total: $570-870/month**

---

## Health Checks

### Backend
```python
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "database": check_db_connection(),
        "redis": check_redis_connection(),
        "llm_api": check_groq_connection()
    }
```

### Kubernetes Probes
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

---

## Rollback Procedure

### Quick Rollback (Kubernetes)
```bash
# Check deployment history
kubectl rollout history deployment/ai-judge-backend -n ai-judge

# Rollback to previous version
kubectl rollout undo deployment/ai-judge-backend -n ai-judge

# Rollback to specific revision
kubectl rollout undo deployment/ai-judge-backend --to-revision=2 -n ai-judge
```

---

## Performance Optimization

### 1. Database Indexing
```sql
CREATE INDEX CONCURRENTLY idx_cases_created_at ON cases(created_at);
ANALYZE cases;
```

### 2. Query Optimization
```python
# Use pagination
@app.get("/api/cases")
def list_cases(skip: int = 0, limit: int = 100):
    return db.query(Case).offset(skip).limit(limit).all()
```

### 3. Response Compression
```python
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### 4. CDN for Static Assets
```bash
# Upload frontend build to S3
aws s3 sync frontend/out s3://ai-judge-static --acl public-read

# Setup CloudFront distribution
aws cloudfront create-distribution --origin-domain-name ai-judge-static.s3.amazonaws.com
```

---

## Compliance & Legal

### GDPR Compliance
- [ ] Data deletion requests
- [ ] Data export functionality
- [ ] Privacy policy
- [ ] Cookie consent
- [ ] Data encryption

### Disclaimer
Add to UI:
```
"This AI Judge is for educational and mock trial purposes only. 
It does not constitute legal advice. Consult a licensed attorney 
for actual legal matters."
```

---

## Support & Maintenance

### Monitoring Alerts
- API latency > 2s
- Error rate > 5%
- CPU usage > 80%
- Memory usage > 90%
- Disk space < 10%
- LLM API failures

### Maintenance Windows
- Weekly: Security updates
- Monthly: Dependency updates
- Quarterly: Major feature releases

---

## Success Metrics

### Technical KPIs
- 99.9% uptime
- < 2s average response time
- < 1% error rate
- < 5min deployment time

### Business KPIs
- 1000+ cases/month
- 40%+ follow-up usage
- 70%+ user satisfaction
- < 10% support ticket rate

---

**Your AI Judge is now production-ready! 🚀⚖️**

For questions or issues, consult the troubleshooting guide or open a GitHub issue.
