# Deployment Guide for AIPY-VN

This guide covers deploying the VietStore RAG application to production.

## Prerequisites

- Docker and Docker Compose installed
- Kubernetes cluster (optional, for K8s deployment)
- Domain name configured
- SSL certificates (for HTTPS)
- Environment variables configured

## Environment Variables

Create a `.env.production` file:

```env
# Database
POSTGRES_USER=your_postgres_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=vietstore

# Redis
REDIS_PASSWORD=your_redis_password

# API
API_URL=https://api.vietstore.vn
CORS_ORIGINS=https://vietstore.vn,https://owner.vietstore.vn,https://admin.vietstore.vn

# Security
JWT_SECRET_KEY=your_jwt_secret_key
ECC_PRIVATE_KEY_PEM=your_ecc_private_key_pem
CSRF_SECRET_KEY=your_csrf_secret_key

# Monitoring
GRAFANA_USER=admin
GRAFANA_PASSWORD=your_grafana_password
GRAFANA_URL=https://grafana.vietstore.vn

# Sentry (Error Tracking)
SENTRY_DSN=your_sentry_dsn
SENTRY_ENVIRONMENT=production

# Docker Registry
DOCKER_REGISTRY=docker.io
IMAGE_TAG=latest
```

## Deployment Methods

### Method 1: Docker Compose (Recommended for small deployments)

#### Development
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### Production
```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Start production services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down
```

### Method 2: Kubernetes (Recommended for large deployments)

#### Prerequisites
- kubectl configured
- Kubernetes cluster running
- NGINX Ingress Controller installed

#### Deploy
```bash
# Apply all configurations
kubectl apply -f k8s/

# Check status
kubectl get pods -n vietstore

# Get services
kubectl get services -n vietstore

# View logs
kubectl logs -f deployment/api-server -n vietstore
```

#### Scale
```bash
# Scale API server
kubectl scale deployment api-server --replicas=3 -n vietstore

# Scale frontend apps
kubectl scale deployment web-customer --replicas=2 -n vietstore
kubectl scale deployment web-owner --replicas=2 -n vietstore
kubectl scale deployment web-admin --replicas=1 -n vietstore
```

### Method 3: CI/CD Deployment

The CI/CD pipeline automatically deploys to:
- **Staging**: When pushing to `develop` branch
- **Production**: When pushing to `master` branch

#### Manual Deployment
```bash
# Deploy to staging
git push origin develop

# Deploy to production
git push origin master
```

## Monitoring

### Prometheus
- URL: `http://localhost:9090` (or your domain)
- Metrics: System metrics, API metrics, custom metrics

### Grafana
- URL: `http://localhost:3003` (or your domain)
- Default credentials: admin/admin (change in production)
- Dashboards: Pre-configured dashboards for monitoring

### Logs
View logs with Docker Compose:
```bash
# API server logs
docker-compose logs -f api-server

# All logs
docker-compose logs -f
```

View logs with Kubernetes:
```bash
# API server logs
kubectl logs -f deployment/api-server -n vietstore

# All pods logs
kubectl logs -f -n vietstore --all-containers=true
```

## SSL/TLS Configuration

### Using Let's Encrypt with Certbot

```bash
# Install certbot
sudo apt-get install certbot

# Generate certificates
sudo certbot certonly --standalone -d vietstore.vn -d api.vietstore.vn

# Copy certificates to nginx/ssl
sudo cp /etc/letsencrypt/live/vietstore.vn/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/vietstore.vn/privkey.pem nginx/ssl/
```

### Using Self-Signed Certificates (Development Only)

```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/privkey.pem \
  -out nginx/ssl/fullchain.pem
```

## Backup and Restore

### Database Backup
```bash
# Backup
docker-compose exec postgres pg_dump -U postgres vietstore > backup.sql

# Restore
docker-compose exec -T postgres psql -U postgres vietstore < backup.sql
```

### Volume Backup
```bash
# Backup volumes
docker run --rm -v vietstore_postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres-backup.tar.gz /data

# Restore volumes
docker run --rm -v vietstore_postgres_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/postgres-backup.tar.gz -C /
```

## Troubleshooting

### Database Connection Issues
```bash
# Check postgres health
docker-compose ps postgres

# Check postgres logs
docker-compose logs postgres

# Restart postgres
docker-compose restart postgres
```

### Redis Connection Issues
```bash
# Check redis health
docker-compose ps redis

# Check redis logs
docker-compose logs redis

# Test redis connection
docker-compose exec redis redis-cli ping
```

### API Server Issues
```bash
# Check API logs
docker-compose logs api-server

# Restart API server
docker-compose restart api-server

# Check environment variables
docker-compose config
```

### Frontend Build Issues
```bash
# Rebuild frontend
docker-compose build web-customer

# Check build logs
docker-compose logs web-customer
```

## Performance Tuning

### PostgreSQL
```yaml
# Add to docker-compose.yml
postgres:
  command:
    - postgres
    - -c
    - shared_buffers=256MB
    - -c
    - effective_cache_size=1GB
    - -c
    - maintenance_work_mem=64MB
    - -c
    - checkpoint_completion_target=0.9
    - -c
    - wal_buffers=16MB
    - -c
    - default_statistics_target=100
    - -c
    - random_page_cost=1.1
    - -c
    - effective_io_concurrency=200
    - -c
    - work_mem=1310kB
    - -c
    - min_wal_size=1GB
    - -c
    - max_wal_size=4GB
```

### Redis
```yaml
# Add to docker-compose.yml
redis:
  command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
```

### API Server
```yaml
# Add to docker-compose.yml
api-server:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 2G
      reservations:
        cpus: '1'
        memory: 1G
```

## Security Checklist

- [ ] Change all default passwords
- [ ] Use strong JWT secret keys
- [ ] Configure ECC private keys
- [ ] Enable HTTPS with valid SSL certificates
- [ ] Configure CORS properly
- [ ] Enable rate limiting
- [ ] Configure firewall rules
- [ ] Enable security headers
- [ ] Set up monitoring and alerting
- [ ] Configure backup strategy
- [ ] Review and update dependencies regularly
- [ ] Enable audit logging
- [ ] Configure Sentry for error tracking

## Support

For issues or questions:
- Check logs: `docker-compose logs -f`
- Check health: `docker-compose ps`
- Review documentation: `docs/`
- Open an issue on GitHub
