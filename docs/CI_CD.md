# CI/CD System Documentation

## Overview

AIPY-VN has a comprehensive CI/CD pipeline that automates testing, building, and deployment processes.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Actions CI/CD                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Security Scan │  │   Backend    │  │   Frontend   │    │
│  │   (safety,    │  │    Tests     │  │    Tests     │    │
│  │  pip-audit,   │  │  (pytest,    │  │  (eslint,    │    │
│  │  bandit,      │  │   coverage)  │  │   prettier)   │    │
│  │  trufflehog)  │  │              │  │              │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                │                  │              │
│         └────────────────┴──────────────────┘              │
│                            │                                 │
│                    ┌───────▼────────┐                        │
│                    │  E2E Tests      │                        │
│                    │  (Playwright)   │                        │
│                    └───────┬────────┘                        │
│                            │                                 │
│                    ┌───────▼────────┐                        │
│                    │  Docker Build   │                        │
│                    │  (Buildx cache) │                        │
│                    └───────┬────────┘                        │
│                            │                                 │
│              ┌─────────────┴─────────────┐                  │
│              │                           │                  │
│         ┌────▼──────┐            ┌──────▼────┐            │
│         │  Staging   │            │ Production │            │
│         │ (develop)  │            │  (master)  │            │
│         └────────────┘            └────────────┘            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Pipeline Stages

### 1. Security Scan
- **Tools**: safety, pip-audit, bandit, trufflehog3
- **Purpose**: Detect security vulnerabilities and secrets
- **Artifacts**: Security reports (JSON format)
- **Status**: Runs on all branches

### 2. Backend Tests
- **Services**: PostgreSQL, Redis, Qdrant
- **Tests**: pytest with coverage
- **Coverage**: Codecov integration
- **Artifacts**: Coverage reports (HTML, XML)
- **Status**: Runs after security scan

### 3. Frontend Tests
- **Matrix**: web-customer, web-owner, web-admin
- **Tests**: ESLint, TypeScript, unit tests, build
- **Artifacts**: Build artifacts
- **Status**: Runs in parallel

### 4. E2E Tests
- **Framework**: Playwright
- **Matrix**: web-customer, web-owner, web-admin
- **Artifacts**: Playwright reports
- **Status**: Runs after backend and frontend tests

### 5. Docker Build
- **Strategy**: Docker Buildx with cache
- **Images**: API server, Customer, Owner, Admin
- **Registry**: Docker Hub (configurable)
- **Tags**: Branch-based and SHA-based
- **Status**: Runs after all tests pass

### 6. Deployment
- **Staging**: Auto-deploy on `develop` branch
- **Production**: Auto-deploy on `master` branch
- **Environment**: GitHub Environments
- **Notifications**: Slack integration
- **Status**: Runs after Docker build

## Pre-commit Hooks

### Installation
```bash
pip install pre-commit
pre-commit install
```

### Hooks
- **Python**: ruff, black, isort, mypy, bandit
- **TypeScript**: eslint, prettier
- **Security**: detect-secrets
- **Docker**: hadolint
- **Custom**: pytest-backend, typecheck-frontend

### Usage
```bash
# Run all hooks
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files

# Skip hooks (not recommended)
git commit --no-verify -m "message"
```

## Deployment Methods

### Docker Compose (Development)
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Docker Compose (Production)
```bash
# Build and start
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down
```

### Kubernetes (Production)
```bash
# Apply all configurations
kubectl apply -f k8s/

# Check status
kubectl get pods -n vietstore

# Scale deployments
kubectl scale deployment api-server --replicas=3 -n vietstore
```

## Monitoring

### Prometheus
- **URL**: http://localhost:9090
- **Metrics**: System, API, custom metrics
- **Configuration**: monitoring/prometheus.yml

### Grafana
- **URL**: http://localhost:3003
- **Credentials**: admin/admin (change in production)
- **Dashboards**: Pre-configured dashboards
- **Datasources**: Prometheus

## Environment Variables

### Required for CI/CD
```yaml
DOCKER_USERNAME: Docker Hub username
DOCKER_PASSWORD: Docker Hub password
SLACK_WEBHOOK: Slack webhook for notifications
```

### Required for Production
```yaml
POSTGRES_USER: PostgreSQL username
POSTGRES_PASSWORD: PostgreSQL password
POSTGRES_DB: Database name
REDIS_PASSWORD: Redis password
JWT_SECRET_KEY: JWT secret key
ECC_PRIVATE_KEY_PEM: ECC private key
CSRF_SECRET_KEY: CSRF secret key
SENTRY_DSN: Sentry DSN
GRAFANA_USER: Grafana username
GRAFANA_PASSWORD: Grafana password
```

## Troubleshooting

### Pipeline Failures

#### Security Scan Failures
- Check security reports in artifacts
- Fix vulnerabilities: Update dependencies
- Remove secrets: Rotate keys, remove from code

#### Backend Test Failures
- Check test logs in GitHub Actions
- Run tests locally: `pytest apps/api-server/tests/ -v`
- Check database connection: Ensure services are healthy

#### Frontend Test Failures
- Check lint errors: Run `npm run lint`
- Check type errors: Run `npm run type-check`
- Check build errors: Run `npm run build`

#### E2E Test Failures
- Check Playwright reports in artifacts
- Run locally: `npm run test:e2e`
- Check API availability: Ensure backend is running

#### Docker Build Failures
- Check Dockerfile syntax
- Check build logs in GitHub Actions
- Verify base images are available

### Deployment Failures

#### Staging Deployment
- Check environment variables
- Check service health: `docker-compose ps`
- Check logs: `docker-compose logs -f`

#### Production Deployment
- Check secrets are configured
- Check registry access
- Check image tags
- Monitor deployment logs

## Best Practices

### Code Quality
- Always run pre-commit hooks before committing
- Ensure tests pass locally before pushing
- Review security scan reports
- Maintain high test coverage (>80%)

### Deployment
- Test in staging before production
- Use feature branches for development
- Review changes before merging to master
- Monitor deployments after push

### Security
- Never commit secrets
- Rotate keys regularly
- Review security reports
- Keep dependencies updated
- Enable security headers

### Monitoring
- Set up alerts for critical metrics
- Review Grafana dashboards regularly
- Check logs for errors
- Monitor system resources
- Set up log aggregation

## CI/CD Secrets Configuration

### GitHub Secrets
Configure these in GitHub repository settings:

```yaml
# Docker Registry
DOCKER_USERNAME: your_dockerhub_username
DOCKER_PASSWORD: your_dockerhub_password

# Notifications
SLACK_WEBHOOK: your_slack_webhook_url

# Production (optional)
PRODUCTION_API_KEY: your_production_api_key
PRODUCTION_SECRET: your_production_secret
```

### Environment Files
Create `.env.production` for production:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=vietstore
REDIS_PASSWORD=secure_redis_password
JWT_SECRET_KEY=secure_jwt_secret
ECC_PRIVATE_KEY_PEM=your_ecc_key
CSRF_SECRET_KEY=secure_csrf_secret
SENTRY_DSN=your_sentry_dsn
GRAFANA_USER=admin
GRAFANA_PASSWORD=secure_grafana_password
```

## Performance Optimization

### CI/CD Pipeline
- Use Docker Buildx cache for faster builds
- Run tests in parallel where possible
- Use matrix strategy for multiple apps
- Cache dependencies (pip, npm)

### Docker Images
- Use multi-stage builds
- Minimize image size
- Use alpine base images
- Layer caching

### Deployment
- Use rolling updates
- Implement health checks
- Use resource limits
- Configure autoscaling

## CI/CD Metrics

### Key Metrics to Track
- Pipeline duration
- Test coverage percentage
- Build success rate
- Deployment success rate
- Security vulnerabilities count
- Test flakiness rate

### Monitoring
- GitHub Actions insights
- Codecov coverage reports
- Prometheus metrics
- Grafana dashboards
- Sentry error tracking

## Resources

### Documentation
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Pre-commit Documentation](https://pre-commit.com/)

### Tools
- [Codecov](https://codecov.io/)
- [Sentry](https://sentry.io/)
- [Grafana](https://grafana.com/)
- [Prometheus](https://prometheus.io/)

### Support
- Check pipeline logs in GitHub Actions
- Review security reports
- Check deployment logs
- Monitor Grafana dashboards
- Review Sentry errors
