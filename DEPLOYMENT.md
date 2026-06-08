# VietStore RAG - Deployment Guide

## Overview

VietStore RAG is a full-stack e-commerce marketplace with AI-powered search, consisting of:
- **Backend**: FastAPI with PostgreSQL, Redis, Qdrant
- **Frontend**: 3 React apps (Customer, Owner, Admin)
- **Security**: ECC cryptography for JWT signing and E2E encryption

## Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)
- Git

## Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd AIPY-VN
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# IMPORTANT: Generate ECC_PRIVATE_KEY_PEM for production
```

### 3. Start Services

```bash
# Start all services (PostgreSQL, Redis, Qdrant, API, Frontends)
docker compose up -d

# Check service status
docker compose ps

# View logs
docker compose logs -f api-server
```

### 4. Database Migrations

```bash
# Run Alembic migrations
cd apps/api-server
alembic upgrade head

# Or run inside Docker
docker compose exec api-server alembic upgrade head
```

### 5. Seed Data (Optional)

```bash
# Seed stores and products
docker compose exec api-server python src/seed.py
```

### 6. Access Applications

- **Customer App**: http://localhost:3000
- **Owner App**: http://localhost:3001
- **Admin App**: http://localhost:3002
- **API Documentation**: http://localhost:9000/docs

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Nginx (Optional)                      │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌──────▼────────┐  ┌──────▼────────┐
│  Web Customer  │  │   Web Owner   │  │   Web Admin   │
│  (React/Vite)   │  │  (React/Vite)  │  │  (React/Vite)  │
│    Port 3000    │  │    Port 3001   │  │    Port 3002   │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
                    ┌───────▼────────┐
                    │  FastAPI API    │
                    │   Port 9000     │
                    └────────┬────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼────────┐ ┌──────▼────────┐ ┌──────▼────────┐
│  PostgreSQL    │ │     Redis      │ │    Qdrant     │
│  (PostGIS)     │ │   (Cache)      │ │  (Vector DB)  │
│   Port 5432     │ │   Port 6379     │ │   Port 6333    │
└────────────────┘ └────────────────┘ └────────────────┘
```

## Services

### PostgreSQL (PostGIS)
- **Port**: 5432
- **Database**: vietstore
- **Features**: Spatial data support for store locations

### Redis
- **Port**: 6379
- **Purpose**: Caching, session storage, rate limiting

### Qdrant
- **Port**: 6333
- **Purpose**: Vector embeddings for AI search

### API Server
- **Port**: 9000
- **Framework**: FastAPI
- **Features**: ECC-signed JWT, E2E encryption, rate limiting

### Web Apps
- **Customer**: Port 3000
- **Owner**: Port 3001
- **Admin**: Port 3002

## Development

### Local Development (without Docker)

#### Backend

```bash
cd apps/api-server

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment
export $(cat .env | xargs)

# Run migrations
alembic upgrade head

# Run server
uvicorn src.main:app --reload --port 9000
```

#### Frontend

```bash
# Customer App
cd apps/web-customer
npm install
npm run dev  # Port 3000

# Owner App
cd apps/web-owner
npm install
npm run dev  # Port 3001

# Admin App
cd apps/web-admin
npm install
npm run dev  # Port 3002
```

### Database Management

```bash
# Create migration
cd apps/api-server
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1

# View migration history
alembic history
```

## Production Deployment

### 1. Generate ECC Keys

```bash
# Generate ECC private key (do this ONCE and keep secure)
python -c "
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)
print(pem.decode())
"
```

Add the generated key to your production `.env`:
```
ECC_PRIVATE_KEY_PEM=-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----
```

### 2. Configure Environment Variables

Update `.env` for production:
```bash
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql+asyncpg://user:password@prod-db:5432/vietstore
CORS_ORIGINS=https://your-domain.com
PRODUCTION_FRONTEND_URL=https://your-domain.com
SENTRY_DSN=your-production-sentry-dsn
```

### 3. Build Docker Images

```bash
# Build all services
docker compose build

# Or build individually
docker compose build api-server
docker compose build web-customer
docker compose build web-owner
docker compose build web-admin
```

### 4. Deploy

Option A: Docker Compose (Simple)
```bash
docker compose up -d
```

Option B: Kubernetes (Scalable)
- Use provided Kubernetes manifests
- Configure ingress, load balancer, auto-scaling

Option C: Cloud Provider
- **AWS**: ECS, RDS, ElastiCache
- **GCP**: Cloud Run, Cloud SQL, Memorystore
- **Azure**: Container Instances, Azure SQL, Redis Cache

### 5. SSL/TLS Configuration

Use Nginx or cloud load balancer for SSL termination.

Example Nginx config:
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://web-customer:3000;
    }
}
```

## Monitoring

### Health Checks

```bash
# API health check
curl http://localhost:9000/health

# Expected response:
{
  "status": "ok",
  "version": "1.0.0",
  "environment": "production",
  "services": {
    "database": "ok",
    "cache": "ok",
    "vector_db": "ok",
    "postgis": "ok"
  }
}
```

### Logs

```bash
# View all logs
docker compose logs -f

# View specific service
docker compose logs -f api-server
docker compose logs -f web-customer
```

### Metrics

- **Sentry**: Error tracking (configure SENTRY_DSN)
- **Prometheus**: Metrics collection (optional)
- **Grafana**: Visualization (optional)

## Security

### ECC Cryptography

- **JWT Signing**: ECDSA with P-256 curve
- **E2E Encryption**: ECDH key exchange + AES-GCM
- **API Signing**: Digital signatures for sensitive requests

### Best Practices

1. **Never commit** `.env` or private keys
2. **Rotate** ECC keys every 90 days
3. **Use** strong passwords for database
4. **Enable** rate limiting in production
5. **Configure** CORS properly
6. **Use** HTTPS in production
7. **Keep** dependencies updated

## Troubleshooting

### Database Connection Failed

```bash
# Check PostgreSQL is running
docker compose ps postgres

# Check logs
docker compose logs postgres

# Restart database
docker compose restart postgres
```

### API Not Responding

```bash
# Check API logs
docker compose logs api-server

# Restart API
docker compose restart api-server

# Check dependencies
docker compose ps
```

### Frontend Build Failed

```bash
# Clear node_modules
rm -rf apps/web-customer/node_modules
rm -rf apps/web-owner/node_modules
rm -rf apps/web-admin/node_modules

# Rebuild
docker compose build web-customer web-owner web-admin
```

## Backup & Restore

### Database Backup

```bash
# Backup
docker compose exec postgres pg_dump -U postgres vietstore > backup.sql

# Restore
docker compose exec -T postgres psql -U postgres vietstore < backup.sql
```

### Volume Backup

```bash
# Backup volumes
docker run --rm -v vietstore_pgdata:/data -v $(pwd):/backup alpine tar czf /backup/pgdata.tar.gz /data

# Restore volumes
docker run --rm -v vietstore_pgdata:/data -v $(pwd):/backup alpine tar xzf /backup/pgdata.tar.gz -C /
```

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.yml
api-server:
  deploy:
    replicas: 3
    resources:
      limits:
        cpus: '2.0'
        memory: 1G
```

### Load Balancing

Use Nginx, HAProxy, or cloud load balancer to distribute traffic.

## Performance Optimization

### Database

- Enable connection pooling
- Add indexes for frequently queried columns
- Use read replicas for reporting

### Cache

- Use Redis for session storage
- Cache API responses
- Implement query result caching

### Frontend

- Enable code splitting
- Use lazy loading for images
- Implement service worker for offline support

## Support

For issues or questions:
- Check logs: `docker compose logs`
- Review documentation: `/docs`
- Open issue on GitHub
