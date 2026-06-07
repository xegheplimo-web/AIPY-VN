from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import os
import logging

from src.api import (
    search,
    stores,
    products,
    owner,
    admin,
    orders,
    cart,
    chat,
    shipping,
    voice,
    notifications,
    tasks,
    payments,
)
from src.api.auth import router as auth_router

# from src.db import init_db  # Using Alembic migrations instead
from src.middleware import (
    LoggingMiddleware,
    setup_error_handlers,
    RateLimitMiddleware,
    AuthMiddleware,
    RequestValidationMiddleware,
)
from src.services.ecc import init_ecc_service
from src.config import config, validate_config
from src.sentry_config import init_sentry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate configuration
    try:
        validate_config()
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise

    # Initialize Sentry
    init_sentry()

    logger.info(f"Starting in {config.environment} mode")

    # Initialize ECC service with existing key or generate new one
    private_key_pem = config.ecc.private_key_pem
    init_ecc_service(private_key_pem)

    # Initialize database (commented out - using Alembic migrations instead)
    # await init_db()

    # Save generated key to environment if not exists (for development)
    if not private_key_pem:
        from src.services.ecc import get_ecc_service

        ecc_service = get_ecc_service()
        os.environ["ECC_PRIVATE_KEY_PEM"] = ecc_service.get_private_key_pem()
        logger.warning(
            "Generated new ECC key pair. Check ECC_PRIVATE_KEY_PEM environment variable."
        )
        logger.warning("IMPORTANT: Save this key securely for production use.")

    yield


app = FastAPI(
    title="VietStore RAG API",
    description="AI-powered local e-commerce marketplace API",
    version="1.0.0",
    lifespan=lifespan,
)

# Production middleware
# app.add_middleware(RequestValidationMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=200, window=60)
# app.add_middleware(AuthMiddleware)

# Response compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:3001",
        "http://localhost:3002",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Signature",
        "X-Timestamp",
        "X-Request-ID",
    ],
)

# Error handlers
setup_error_handlers(app)

# API v1 routes (versioned)
api_v1_prefix = "/api/v1"
app.include_router(search, prefix=api_v1_prefix)
app.include_router(stores, prefix=api_v1_prefix)
app.include_router(products, prefix=api_v1_prefix)
app.include_router(owner, prefix=api_v1_prefix)
app.include_router(admin, prefix=api_v1_prefix)
app.include_router(orders, prefix=api_v1_prefix)
app.include_router(cart, prefix=api_v1_prefix)
app.include_router(chat, prefix=api_v1_prefix)
app.include_router(shipping.router, prefix=api_v1_prefix)
app.include_router(voice.router, prefix=api_v1_prefix)
app.include_router(notifications.router, prefix=api_v1_prefix)
app.include_router(tasks.router, prefix=api_v1_prefix)
app.include_router(payments.router, prefix=api_v1_prefix)
app.include_router(auth_router, prefix=api_v1_prefix)

# Legacy routes (backward compatibility - no prefix)
app.include_router(search)
app.include_router(stores)
app.include_router(products)
app.include_router(owner)
app.include_router(admin)
app.include_router(orders)
app.include_router(cart)
app.include_router(chat)
app.include_router(shipping.router)
app.include_router(voice.router)
app.include_router(notifications.router)
app.include_router(tasks.router)
app.include_router(payments.router)
app.include_router(auth_router)


@app.get("/health")
async def health_check():
    """Health check endpoint with system status."""
    from src.cache import cache
    from src.vector_db import vector_db
    from src.config import config

    return {
        "status": "ok",
        "version": "1.0.0",
        "environment": config.environment,
        "services": {
            "database": "connected",
            "cache": "connected" if cache.client else "disabled",
            "vector_db": "connected" if vector_db.client else "disabled",
        },
        "timestamp": "2026-06-07T21:00:00Z",
    }
