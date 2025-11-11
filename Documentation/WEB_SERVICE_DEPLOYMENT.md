# RhymeRarity Web Service Deployment Guide

**Complete guide for deploying RhymeRarity as a production web service**

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Local Development Setup](#local-development-setup)
4. [Production Deployment](#production-deployment)
5. [Docker Deployment](#docker-deployment)
6. [Cloud Deployment](#cloud-deployment)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Performance Tuning](#performance-tuning)
9. [Security Considerations](#security-considerations)
10. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   Web Server    │    │   Database      │
│   (Nginx)       │───▶│   (FastAPI)     │───▶│   (SQLite)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Datamuse API  │
                       │   (External)    │
                       └─────────────────┘
```

### Technology Stack

- **Web Framework**: FastAPI (async, high-performance)
- **Database**: SQLite with connection pooling
- **Caching**: Redis (optional)
- **Load Balancer**: Nginx
- **Container**: Docker
- **Monitoring**: Prometheus + Grafana (optional)

---

## Prerequisites

### System Requirements

- **CPU**: 2+ cores (4+ recommended for production)
- **RAM**: 4GB minimum (8GB+ recommended)
- **Storage**: 10GB+ (for database and logs)
- **OS**: Linux (Ubuntu 20.04+ recommended)

### Software Requirements

- Python 3.8+
- Node.js 16+ (for frontend build)
- Docker (optional)
- Nginx (for production)

---

## Local Development Setup

### 1. Clone and Setup

```bash
git clone <repository-url>
cd RhymeRarity
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Ensure database exists
ls data/words_index.sqlite

# If missing, build it
python scripts/build_words_index.py
```

### 3. Configuration

```bash
# Copy default configuration
cp config.json config_local.json

# Edit for local development
nano config_local.json
```

**Local Development Config:**

```json
{
  "database": {
    "path": "data/words_index.sqlite",
    "pool_size": 5,
    "timeout": 30.0
  },
  "api": {
    "timeout": 5.0,
    "max_retries": 3,
    "max_concurrent_requests": 10
  },
  "performance": {
    "enable_caching": true,
    "cache_size": 500,
    "enable_connection_pooling": true,
    "enable_concurrent_requests": true,
    "enable_async_operations": true
  },
  "search": {
    "max_items": 100,
    "min_score": 0.35
  },
  "logging": {
    "level": "DEBUG",
    "log_file": "logs/app.log"
  }
}
```

### 4. Run Development Server

```bash
# Run with auto-reload
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Or run the Gradio app
python app.py
```

### 5. Test API

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test search endpoint
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"word": "double", "use_datamuse": true}'
```

---

## Production Deployment

### 1. FastAPI Web Service

Create `web_service.py`:

```python
#!/usr/bin/env python3
"""
FastAPI Web Service for RhymeRarity
Production-ready async web service
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import asyncio
import logging
import time
from contextlib import asynccontextmanager

from rhyme_core.engine import search_rhymes
from rhyme_core.config import load_config
from rhyme_core.validation import InputValidator
from rhyme_core.exceptions import ValidationError, DatabaseError, APIError
from rhyme_core.error_handler import configure_error_handling

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
)
logger = logging.getLogger(__name__)

# Global configuration
config = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global config
    
    # Startup
    logger.info("Starting RhymeRarity Web Service")
    config = load_config("config.json", preset="production")
    configure_error_handling(enable_graceful_degradation=True)
    logger.info("Service initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down RhymeRarity Web Service")

# Create FastAPI app
app = FastAPI(
    title="RhymeRarity API",
    description="Anti-LLM Rhyme Generation System",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Request/Response Models
class SearchRequest(BaseModel):
    word: str = Field(..., description="Word to find rhymes for", min_length=1, max_length=50)
    syl_filter: str = Field("Any", description="Syllable count filter")
    stress_filter: str = Field("Any", description="Stress pattern filter")
    use_datamuse: bool = Field(True, description="Enable Datamuse API")
    multisyl_only: bool = Field(False, description="Only multi-syllable rhymes")
    enable_alliteration: bool = Field(True, description="Enable alliteration bonus")

class SearchResponse(BaseModel):
    word: str
    results: Dict[str, Any]
    metadata: Dict[str, Any]
    search_time: float

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: float
    uptime: float

# Global variables for health monitoring
start_time = time.time()

# API Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=time.time(),
        uptime=time.time() - start_time
    )

@app.post("/search", response_model=SearchResponse)
async def search_rhymes_endpoint(request: SearchRequest):
    """Main rhyme search endpoint"""
    start_time = time.time()
    
    try:
        # Validate input
        validated_params = InputValidator.validate_search_parameters(
            target_word=request.word,
            syl_filter=request.syl_filter,
            stress_filter=request.stress_filter,
            use_datamuse=request.use_datamuse,
            multisyl_only=request.multisyl_only,
            enable_alliteration=request.enable_alliteration
        )
        
        # Perform search
        results = search_rhymes(
            target_word=validated_params[0],
            syl_filter=validated_params[1],
            stress_filter=validated_params[2],
            use_datamuse=validated_params[3],
            multisyl_only=validated_params[4],
            enable_alliteration=validated_params[5],
            config=config
        )
        
        search_time = time.time() - start_time
        
        return SearchResponse(
            word=validated_params[0],
            results=results,
            metadata={
                "search_time": search_time,
                "total_results": sum(len(cat.get('popular', [])) + len(cat.get('technical', [])) 
                                   for cat in results.get('perfect', {}).values()) +
                               sum(len(cat.get('popular', [])) + len(cat.get('technical', [])) 
                                   for slant_cat in results.get('slant', {}).values() 
                                   for cat in slant_cat.values()) +
                               len(results.get('colloquial', [])),
                "filters_applied": {
                    "syllable": validated_params[1],
                    "stress": validated_params[2],
                    "datamuse": validated_params[3],
                    "multisyl_only": validated_params[4],
                    "alliteration": validated_params[5]
                }
            },
            search_time=search_time
        )
        
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid input: {e}")
    
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=503, detail="Database temporarily unavailable")
    
    except APIError as e:
        logger.error(f"API error: {e}")
        raise HTTPException(status_code=503, detail="External API temporarily unavailable")
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/stats")
async def get_stats():
    """Get service statistics"""
    from rhyme_core.error_handler import get_error_handler
    
    error_handler = get_error_handler()
    error_stats = error_handler.get_error_stats()
    
    return {
        "uptime": time.time() - start_time,
        "error_counts": error_stats['error_counts'],
        "total_errors": error_stats['total_errors'],
        "config": {
            "database_pool_size": config.database.pool_size,
            "api_timeout": config.api.timeout,
            "caching_enabled": config.performance.enable_caching
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "web_service:app",
        host="0.0.0.0",
        port=8000,
        workers=4,
        log_level="info"
    )
```

### 2. Nginx Configuration

Create `/etc/nginx/sites-available/rhymerarity`:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL Configuration
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    # Proxy to FastAPI
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # Health check endpoint (no rate limiting)
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
    
    # Static files (if any)
    location /static/ {
        alias /path/to/static/files/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 3. Systemd Service

Create `/etc/systemd/system/rhymerarity.service`:

```ini
[Unit]
Description=RhymeRarity Web Service
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/path/to/RhymeRarity
Environment=PATH=/path/to/RhymeRarity/venv/bin
ExecStart=/path/to/RhymeRarity/venv/bin/uvicorn web_service:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/path/to/RhymeRarity/logs

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
```

### 4. Production Configuration

Create `config_production.json`:

```json
{
  "database": {
    "path": "/var/lib/rhymerarity/data/words_index.sqlite",
    "pool_size": 20,
    "timeout": 30.0,
    "journal_mode": "WAL",
    "synchronous": "NORMAL",
    "cache_size": -128000,
    "temp_store": "MEMORY"
  },
  "api": {
    "timeout": 5.0,
    "max_retries": 3,
    "backoff_factor": 1.0,
    "rate_limit_delay": 2.0,
    "max_concurrent_requests": 50,
    "user_agent": "RhymeRarity/1.0"
  },
  "performance": {
    "enable_caching": true,
    "cache_size": 5000,
    "enable_connection_pooling": true,
    "enable_concurrent_requests": true,
    "enable_async_operations": true
  },
  "search": {
    "zipf_min_perfect": 0.0,
    "zipf_max_perfect": 6.0,
    "max_perfect_popular": 20,
    "max_perfect_technical": 30,
    "zipf_min_slant": 0.0,
    "zipf_max_slant": 6.0,
    "max_slant_near": 50,
    "max_slant_assonance": 40,
    "max_colloquial": 15,
    "max_items": 500,
    "min_score": 0.35,
    "enable_alliteration_bonus": true,
    "enable_multisyl_bonus": true
  },
  "logging": {
    "level": "INFO",
    "log_file": "/var/log/rhymerarity/app.log",
    "max_file_size": 10485760,
    "backup_count": 10,
    "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
  }
}
```

### 5. Deployment Script

Create `deploy.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Deploying RhymeRarity Web Service"

# Configuration
APP_DIR="/var/www/rhymerarity"
SERVICE_NAME="rhymerarity"
NGINX_SITE="rhymerarity"

# Create application directory
sudo mkdir -p $APP_DIR
sudo chown -R www-data:www-data $APP_DIR

# Copy application files
sudo cp -r . $APP_DIR/
cd $APP_DIR

# Create virtual environment
sudo -u www-data python3 -m venv venv
sudo -u www-data venv/bin/pip install -r requirements.txt

# Create necessary directories
sudo mkdir -p /var/lib/rhymerarity/data
sudo mkdir -p /var/log/rhymerarity
sudo chown -R www-data:www-data /var/lib/rhymerarity
sudo chown -R www-data:www-data /var/log/rhymerarity

# Copy configuration
sudo cp config_production.json config.json

# Enable and start service
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

# Configure Nginx
sudo cp nginx.conf /etc/nginx/sites-available/$NGINX_SITE
sudo ln -sf /etc/nginx/sites-available/$NGINX_SITE /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Check service status
sudo systemctl status $SERVICE_NAME

echo "✅ Deployment complete!"
echo "Service URL: https://your-domain.com"
echo "Health check: https://your-domain.com/health"
```

---

## Docker Deployment

### 1. Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "web_service:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 2. Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  rhymerarity:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data:ro
      - ./logs:/app/logs
      - ./config.json:/app/config.json:ro
    environment:
      - PYTHONPATH=/app
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '2.0'
        reservations:
          memory: 512M
          cpus: '1.0'

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - rhymerarity
    restart: unless-stopped

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

### 3. Docker Deployment Commands

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f rhymerarity

# Scale service
docker-compose up -d --scale rhymerarity=3

# Update service
docker-compose pull
docker-compose up -d
```

---

## Cloud Deployment

### AWS Deployment

#### 1. EC2 Instance

```bash
# Launch EC2 instance (t3.medium or larger)
# Install Docker
sudo yum update -y
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 2. Application Load Balancer

```yaml
# ALB configuration
TargetGroup:
  Type: AWS::ElasticLoadBalancingV2::TargetGroup
  Properties:
    Name: rhymerarity-tg
    Port: 8000
    Protocol: HTTP
    VpcId: !Ref VPC
    HealthCheckPath: /health
    HealthCheckIntervalSeconds: 30
    HealthCheckTimeoutSeconds: 5
    HealthyThresholdCount: 2
    UnhealthyThresholdCount: 3
```

### Google Cloud Platform

#### 1. Cloud Run

```yaml
# cloudbuild.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/rhymerarity', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/rhymerarity']
  - name: 'gcr.io/cloud-builders/gcloud'
    args: [
      'run', 'deploy', 'rhymerarity',
      '--image', 'gcr.io/$PROJECT_ID/rhymerarity',
      '--platform', 'managed',
      '--region', 'us-central1',
      '--allow-unauthenticated',
      '--memory', '1Gi',
      '--cpu', '2',
      '--max-instances', '10'
    ]
```

### Azure Container Instances

```yaml
# azure-deploy.yaml
apiVersion: 2018-10-01
location: eastus
name: rhymerarity
properties:
  containers:
  - name: rhymerarity
    properties:
      image: your-registry/rhymerarity:latest
      resources:
        requests:
          cpu: 2
          memoryInGb: 1
      ports:
      - port: 8000
        protocol: TCP
  osType: Linux
  restartPolicy: Always
  ipAddress:
    type: Public
    ports:
    - protocol: TCP
      port: 8000
```

---

## Monitoring and Logging

### 1. Prometheus Metrics

Create `metrics.py`:

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

# Metrics
REQUEST_COUNT = Counter('rhymerarity_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('rhymerarity_request_duration_seconds', 'Request duration')
ACTIVE_CONNECTIONS = Gauge('rhymerarity_active_connections', 'Active database connections')
SEARCH_RESULTS = Histogram('rhymerarity_search_results', 'Number of search results')

# Add to web_service.py
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.observe(duration)
    
    return response
```

### 2. Grafana Dashboard

```json
{
  "dashboard": {
    "title": "RhymeRarity Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(rhymerarity_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(rhymerarity_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
```

### 3. Log Aggregation

```yaml
# Filebeat configuration
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/rhymerarity/*.log
  fields:
    service: rhymerarity
  fields_under_root: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "rhymerarity-%{+yyyy.MM.dd}"
```

---

## Performance Tuning

### 1. Database Optimization

```sql
-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_words_k3 ON words(k3);
CREATE INDEX IF NOT EXISTS idx_words_k2 ON words(k2);
CREATE INDEX IF NOT EXISTS idx_words_k1 ON words(k1);
CREATE INDEX IF NOT EXISTS idx_words_zipf ON words(zipf);
CREATE INDEX IF NOT EXISTS idx_words_syls ON words(syls);

-- Analyze database for query optimization
ANALYZE;
```

### 2. Connection Pool Tuning

```python
# High-performance configuration
config.database.pool_size = 50
config.database.cache_size = -256000  # 256MB
config.database.journal_mode = "WAL"
config.database.synchronous = "NORMAL"
```

### 3. Caching Strategy

```python
# Redis caching
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_search_results(word: str, results: dict, ttl: int = 3600):
    key = f"search:{hash(word)}"
    redis_client.setex(key, ttl, json.dumps(results))

def get_cached_results(word: str) -> Optional[dict]:
    key = f"search:{hash(word)}"
    cached = redis_client.get(key)
    return json.loads(cached) if cached else None
```

---

## Security Considerations

### 1. Input Validation

```python
# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/search")
@limiter.limit("10/minute")
async def search_rhymes_endpoint(request: Request, search_request: SearchRequest):
    # Implementation
```

### 2. Authentication (Optional)

```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != "your-secret-token":
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials.credentials

@app.post("/search")
async def search_rhymes_endpoint(
    request: SearchRequest,
    token: str = Depends(verify_token)
):
    # Implementation
```

### 3. HTTPS Configuration

```nginx
# SSL/TLS configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
```

---

## Troubleshooting

### Common Issues

1. **High Memory Usage**
   ```bash
   # Check memory usage
   docker stats
   
   # Reduce cache size
   config.performance.cache_size = 100
   ```

2. **Database Locked**
   ```bash
   # Check for long-running queries
   sqlite3 data/words_index.sqlite "SELECT * FROM sqlite_master WHERE type='table';"
   
   # Restart service
   sudo systemctl restart rhymerarity
   ```

3. **API Rate Limiting**
   ```bash
   # Check Datamuse API status
   curl -I https://api.datamuse.com/words?rel_rhy=test
   
   # Enable graceful degradation
   configure_error_handling(enable_graceful_degradation=True)
   ```

4. **Slow Response Times**
   ```bash
   # Check database performance
   sqlite3 data/words_index.sqlite "EXPLAIN QUERY PLAN SELECT * FROM words WHERE k3 = 'AH1|B AH0 L';"
   
   # Optimize configuration
   config.database.pool_size = 20
   config.performance.enable_caching = True
   ```

### Monitoring Commands

```bash
# Check service status
sudo systemctl status rhymerarity

# View logs
sudo journalctl -u rhymerarity -f

# Check database
sqlite3 data/words_index.sqlite "SELECT COUNT(*) FROM words;"

# Test API
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"word": "test"}'
```

---

## Conclusion

This deployment guide provides a comprehensive approach to deploying RhymeRarity as a production web service. The system is designed to be:

- **Scalable**: Horizontal scaling with load balancers
- **Reliable**: Health checks, monitoring, and error handling
- **Secure**: Input validation, rate limiting, and HTTPS
- **Performant**: Connection pooling, caching, and optimization
- **Maintainable**: Logging, metrics, and monitoring

Choose the deployment method that best fits your infrastructure and requirements. For production use, we recommend the Docker deployment with Nginx load balancing for optimal performance and reliability.

**Happy deploying! 🚀**


