# VietStore RAG - Quick Start Guide

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (optional for local dev)
- Python 3.11+ (optional for local dev)

### Method 1: Docker (Recommended)

```bash
# 1. Clone repository
git clone <repository-url>
cd AIPY-VN

# 2. Start services
docker compose up -d

# 3. Run database migrations
docker compose exec api-server alembic upgrade head

# 4. Seed test data
docker compose exec api-server python seed_test_data.py

# 5. Access applications
# Customer: http://localhost:3000
# Owner: http://localhost:3001
# Admin: http://localhost:3002
# API Docs: http://localhost:9000/docs
```

### Method 2: Local Development

#### Backend
```bash
cd apps/api-server

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment
export $(cat .env | xargs)

# Run migrations
alembic upgrade head

# Seed data
python seed_test_data.py

# Run server
uvicorn src.main:app --reload --port 9000
```

#### Frontend (Customer)
```bash
cd apps/web-customer
npm install
npm run dev  # Port 3000
```

#### Frontend (Owner)
```bash
cd apps/web-owner
npm install
npm run dev  # Port 3001
```

#### Frontend (Admin)
```bash
cd apps/web-admin
npm install
npm run dev  # Port 3002
```

## 📁 Project Structure

```
AIPY-VN/
├── apps/
│   ├── api-server/          # FastAPI backend
│   │   ├── src/
│   │   │   ├── api/         # API endpoints
│   │   │   ├── models/      # Database models
│   │   │   ├── services/    # Business logic
│   │   │   └── main.py
│   │   ├── alembic/         # Database migrations
│   │   └── seed_test_data.py
│   ├── web-customer/        # React customer app
│   │   ├── src/
│   │   │   ├── contexts/    # Auth, Cart contexts
│   │   │   ├── services/    # API service
│   │   │   └── pages/       # Page components
│   ├── web-owner/           # React owner app
│   └── web-admin/           # React admin app
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── .pre-commit-config.yaml
├── .github/workflows/
│   └── ci-cd.yml
├── nginx/
│   └── nginx.conf
├── docs/
│   ├── CI_CD.md
│   ├── PRE_COMMIT.md
│   └── DEMO_DATA_REPORT.md
├── DEPLOYMENT.md
└── README.md
```

## 🔐 Test Accounts

After seeding, you can use these test accounts:

**Customer:**
- Email: customer@example.com
- Password: password123

**Owner:**
- Email: owner@example.com
- Password: password123

**Admin:**
- Email: admin@example.com
- Password: password123

## 🎯 Features

### Customer App
- AI-powered product search
- Store locator with maps
- Shopping cart with store grouping
- Checkout wizard
- Order tracking
- Store chat

### Owner App
- Dashboard with analytics
- Product management
- Bulk upload (CSV/Excel)
- Order management
- Customer chat
- Promotions & discounts

### Admin App
- Store verification
- Match queue (seed vs registered)
- User management
- Report moderation
- Category management
- System health monitoring

## 🔧 Common Commands

### Docker
```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# View logs
docker compose logs -f api-server

# Restart service
docker compose restart api-server

# Run command in container
docker compose exec api-server alembic upgrade head
```

### Database
```bash
# Create migration
cd apps/api-server
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1

# View history
alembic history
```

### Frontend
```bash
# Install dependencies
npm install

# Run dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit
pre-commit install

# Run all hooks
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files
```

## 📚 Documentation

- [Deployment Guide](DEPLOYMENT.md) - Full deployment instructions
- [CI/CD Documentation](docs/CI_CD.md) - CI/CD pipeline and deployment system
- [Pre-commit Hooks](docs/PRE_COMMIT.md) - Code quality and pre-commit configuration
- [API Documentation](http://localhost:9000/docs) - Interactive API docs
- [AGENTS.md](AGENTS.md) - Development guidelines

## 🐛 Troubleshooting

### Database connection failed
```bash
# Check PostgreSQL is running
docker compose ps postgres

# Restart database
docker compose restart postgres
```

### API not responding
```bash
# Check API logs
docker compose logs api-server

# Restart API
docker compose restart api-server
```

### Frontend build failed
```bash
# Clear node_modules and reinstall
rm -rf node_modules
npm install
```

## 🤝 Contributing

1. Install pre-commit hooks: `pre-commit install`
2. Create a feature branch
3. Make your changes
4. Run pre-commit hooks: `pre-commit run --all-files`
5. Test thoroughly
6. Submit a pull request

## 📊 CI/CD

The project uses GitHub Actions for CI/CD:
- Automated testing on every push
- Security scanning
- Docker image building
- Automated deployment to staging (develop branch)
- Automated deployment to production (master branch)

See [docs/CI_CD.md](docs/CI_CD.md) for details.

## 📄 License

MIT License - see LICENSE file for details
