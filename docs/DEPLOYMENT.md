# Deployment Guide - Dance Movement Analyzer

## 🚀 Deployment Options

This guide covers multiple deployment strategies for the Dance Movement Analyzer.

---

## Option 1: Docker Deployment (Recommended)

### Prerequisites
- Docker 20.10+
- Docker Compose 1.29+
- 4GB RAM minimum
- 10GB disk space

### Quick Start

```bash
# 1. Clone repository
git clone https://github.com/Prathameshv07/Dance-Movement-Analyzer
cd dance-movement-analyzer

# 2. Build Docker image
docker-compose build

# 3. Run container
docker-compose up -d

# 4. Check status
docker-compose ps
docker-compose logs -f
```

### Access Application
- **Frontend**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/health

### Docker Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f dance-analyzer

# Restart service
docker-compose restart

# Rebuild after code changes
docker-compose build --no-cache
docker-compose up -d

# Clean up
docker-compose down -v  # Removes volumes
docker system prune -a  # Clean unused images
```

---

## Option 2: Hugging Face Spaces

### Setup

1. **Create Space**
   - Go to https://huggingface.co/spaces
   - Click "Create new Space"
   - Choose Docker SDK
   - Name: dance-movement-analyzer

2. **Prepare Files**

Create `Dockerfile` in root:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx libglib2.0-0 libsm6 \
    libxext6 libxrender-dev libgomp1 ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/app /app/app
COPY frontend /app/frontend

# Create directories
RUN mkdir -p /app/uploads /app/outputs

EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
```

3. **Push to Space**
```bash
git init
git remote add space https://huggingface.co/spaces/prathameshv07/Dance-Movement-Analyzer
git add .
git commit -m "Initial deployment"
git push --force space main
```

4. **Configure Space**
   - Set visibility (Public/Private)
   - Add README with usage instructions
   - Configure hardware (CPU/GPU)

---

## Option 3: AWS EC2

### Launch Instance

1. **Choose AMI**: Ubuntu 22.04 LTS
2. **Instance Type**: t3.medium (2 vCPU, 4GB RAM) minimum
3. **Storage**: 20GB EBS volume
4. **Security Group**: 
   - SSH (22) from your IP
   - HTTP (80) from anywhere
   - Custom TCP (8000) from anywhere

### Setup Script

SSH into instance and run:

```bash
#!/bin/bash

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone repository
git clone https://github.com/Prathameshv07/Dance-Movement-Analyzer
cd dance-movement-analyzer

# Start services
docker-compose up -d

# Setup nginx reverse proxy (optional)
sudo apt-get install -y nginx
sudo tee /etc/nginx/sites-available/dance-analyzer << EOF
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/dance-analyzer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### SSL Certificate (Let's Encrypt)

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

---

## Option 4: Google Cloud Run

### Prerequisites
- Google Cloud account
- gcloud CLI installed

### Deployment

```bash
# 1. Set project
gcloud config set project YOUR_PROJECT_ID

# 2. Build and push image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/dance-analyzer

# 3. Deploy to Cloud Run
gcloud run deploy dance-analyzer \
  --image gcr.io/YOUR_PROJECT_ID/dance-analyzer \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --timeout 300s \
  --max-instances 10
```

---

## Option 5: DigitalOcean App Platform

### Setup

1. **Create App**
   - Go to DigitalOcean App Platform
   - Connect GitHub repository
   - Select branch

2. **Configure Build**
   - Build Command: `docker build -t dance-analyzer .`
   - Run Command: `uvicorn app.main:app --host 0.0.0.0 --port 8080`

3. **Environment Variables**
```
API_HOST=0.0.0.0
API_PORT=8080
MAX_FILE_SIZE=104857600
```

4. **Resources**
   - Basic: 1 GB RAM, 1 vCPU
   - Pro: 2 GB RAM, 2 vCPU (recommended)

---

## Environment Variables

### Production Configuration

```bash
# API Settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Security
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# File Limits
MAX_FILE_SIZE=104857600
MAX_VIDEO_DURATION=60

# Processing
MEDIAPIPE_MODEL_COMPLEXITY=1
MEDIAPIPE_MIN_DETECTION_CONFIDENCE=0.5
MAX_WORKERS=2

# Storage
UPLOAD_DIR=/app/uploads
OUTPUT_DIR=/app/outputs
LOG_DIR=/app/logs

# Session Management
SESSION_CLEANUP_INTERVAL=3600
MAX_SESSIONS=50
```

---

## Performance Optimization

### 1. Increase Workers

```yaml
# docker-compose.yml
environment:
  - MAX_WORKERS=4  # Increase for more concurrent processing
```

### 2. Use GPU (if available)

```dockerfile
# Dockerfile
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Install TensorFlow GPU
RUN pip install tensorflow-gpu mediapipe-gpu
```

### 3. Enable Caching

```python
# app/config.py
CACHE_ENABLED = True
CACHE_DIR = "/app/cache"
CACHE_MAX_SIZE = 10737418240  # 10GB
```

### 4. CDN for Static Files

```nginx
# nginx.conf
location /static/ {
    alias /app/frontend/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

---

## Monitoring & Logging

### 1. Health Checks

```bash
# Check application health
curl http://localhost:8000/health

# Monitor logs
docker-compose logs -f --tail=100
```

### 2. Prometheus Metrics

Add to `main.py`:
```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

### 3. Log Aggregation

```yaml
# docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

---

## Backup & Recovery

### Backup Data

```bash
# Backup uploads and outputs
docker run --rm \
  -v dance-movement-analyzer_uploads:/uploads \
  -v dance-movement-analyzer_outputs:/outputs \
  -v $(pwd)/backup:/backup \
  alpine \
  tar czf /backup/data-$(date +%Y%m%d).tar.gz /uploads /outputs
```

### Restore Data

```bash
# Restore from backup
docker run --rm \
  -v dance-movement-analyzer_uploads:/uploads \
  -v dance-movement-analyzer_outputs:/outputs \
  -v $(pwd)/backup:/backup \
  alpine \
  tar xzf /backup/data-YYYYMMDD.tar.gz -C /
```

---

## Security Best Practices

### 1. Use Secrets

```yaml
# docker-compose.yml
secrets:
  api_key:
    file: ./secrets/api_key.txt

services:
  dance-analyzer:
    secrets:
      - api_key
```

### 2. Enable HTTPS

```python
# main.py
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(HTTPSRedirectMiddleware)
```

### 3. Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/upload")
@limiter.limit("5/minute")
async def upload_video():
    pass
```

### 4. Input Validation

All inputs are validated. Ensure:
- File size limits enforced
- File types restricted
- Path traversal prevented
- SQL injection not applicable (no DB)

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs dance-analyzer

# Common issues:
# 1. Port already in use
docker ps -a
sudo lsof -i :8000

# 2. Permission denied
sudo chown -R 1000:1000 uploads outputs logs

# 3. Out of memory
docker stats
# Increase memory limit in docker-compose.yml
```

### High CPU Usage

```bash
# Check resource usage
docker stats dance-analyzer

# Reduce model complexity
# Edit docker-compose.yml
environment:
  - MEDIAPIPE_MODEL_COMPLEXITY=0
```

### Slow Processing

```bash
# Increase workers
environment:
  - MAX_WORKERS=4

# Use GPU if available
# Requires nvidia-docker
```

---

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.yml
services:
  dance-analyzer:
    deploy:
      replicas: 3
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    depends_on:
      - dance-analyzer
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

### Load Balancer Configuration

```nginx
upstream dance_analyzer {
    least_conn;
    server dance-analyzer-1:8000;
    server dance-analyzer-2:8000;
    server dance-analyzer-3:8000;
}

server {
    listen 80;
    
    location / {
        proxy_pass http://dance_analyzer;
    }
}
```

---

## Cost Optimization

### Cloud Costs

| Platform | Cost/Month | Notes |
|----------|-----------|-------|
| Hugging Face Spaces | Free - $15 | Good for demos |
| AWS EC2 t3.medium | $30 - $35 | Pay for compute |
| Google Cloud Run | $10 - $50 | Pay per use |
| DigitalOcean App | $12 - $24 | Fixed pricing |

### Optimization Tips

1. **Use spot instances** (AWS, GCP)
2. **Auto-scaling** based on demand
3. **Session cleanup** to free resources
4. **Caching** to reduce processing
5. **CDN** for static files

---

## CI/CD Pipeline

### GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Build and push Docker image
        run: |
          docker build -t dance-analyzer .
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker tag dance-analyzer ${{ secrets.DOCKER_USERNAME }}/dance-analyzer:latest
          docker push ${{ secrets.DOCKER_USERNAME }}/dance-analyzer:latest
      
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /app/dance-movement-analyzer
            docker-compose pull
            docker-compose up -d
```

---

## Maintenance

### Regular Tasks

```bash
# Weekly: Clean old sessions
docker exec dance-analyzer python -c "
from app.utils import cleanup_old_sessions
cleanup_old_sessions(max_age_hours=168)
"

# Monthly: Update dependencies
docker-compose build --no-cache
docker-compose up -d

# As needed: Backup data
./scripts/backup.sh
```

---

## Support & Monitoring

### Set Up Alerts

```yaml
# docker-compose.yml
services:
  dance-analyzer:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Monitor Metrics

- Response time
- Error rate
- Active sessions
- Memory usage
- Disk space

---

## Success Checklist

- [ ] Application builds successfully
- [ ] Docker container runs
- [ ] Health check passes
- [ ] Can upload video
- [ ] Processing works
- [ ] Can download result
- [ ] HTTPS configured (production)
- [ ] Monitoring set up
- [ ] Backups configured
- [ ] Documentation updated

---

## Next Steps

1. **Test deployment** thoroughly
2. **Set up monitoring**
3. **Configure backups**
4. **Optimize performance**
5. **Scale as needed**

---