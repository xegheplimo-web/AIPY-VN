from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import os
import logging
import asyncio

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
from src.api.reviews import router as reviews
from src.api.profile import router as profile
from src.api.categories import router as categories
from src.api.favorites import router as favorites

# from src.db import init_db  # Using Alembic migrations instead
from src.middleware import (
    LoggingMiddleware,
    setup_error_handlers,
    RateLimitMiddleware,
    AuthMiddleware,
    RequestValidationMiddleware,
    CSRFMiddleware,
    BodySizeLimitMiddleware,
)
from src.services.ecc import init_ecc_service, get_e2e_service
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
            "Generated new ECC key pair. Save ECC_PRIVATE_KEY_PEM environment variable securely."
        )
        logger.warning(
            "IMPORTANT: In production, set ECC_PRIVATE_KEY_PEM in your environment configuration."
        )

    # Start background task for session key cleanup
    async def cleanup_session_keys():
        """Periodically cleanup expired session keys."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                e2e_service = get_e2e_service()
                e2e_service.cleanup_expired_sessions()
            except Exception as e:
                logger.error(f"Session key cleanup error: {e}", exc_info=True)

    # Start the cleanup task
    cleanup_task = asyncio.create_task(cleanup_session_keys())

    yield

    # Cleanup on shutdown
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="VietStore RAG API",
    description="AI-powered local e-commerce marketplace API",
    version="1.0.0",
    lifespan=lifespan,
)

# Production middleware
app.add_middleware(RequestValidationMiddleware)
app.add_middleware(BodySizeLimitMiddleware, max_size=10 * 1024 * 1024)  # 10MB
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=200, window=60)

# Enable authentication middleware in production
if config.is_production:
    app.add_middleware(AuthMiddleware)
    logger.info("Authentication middleware enabled")
else:
    logger.warning("Authentication middleware disabled in development mode")

# Enable CSRF protection in production
if config.is_production:
    app.add_middleware(
        CSRFMiddleware,
        secret_key=(
            config.csrf_secret_key if hasattr(config, "csrf_secret_key") else None
        ),
    )
    logger.info("CSRF middleware enabled")
else:
    logger.warning("CSRF middleware disabled in development mode")

# Response compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Parse CORS origins from config
cors_origins = (
    config.cors_origins.split(",")
    if config.cors_origins
    else [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:3001",
        "http://localhost:3002",
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        cors_origins
        if config.is_development
        else (
            [config.production_frontend_url]
            if hasattr(config, "production_frontend_url")
            else cors_origins
        )
    ),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Signature",
        "X-Timestamp",
        "X-Request-ID",
        "X-CSRF-Token",
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
app.include_router(shipping, prefix=api_v1_prefix)
app.include_router(voice, prefix=api_v1_prefix)
app.include_router(notifications, prefix=api_v1_prefix)
app.include_router(tasks, prefix=api_v1_prefix)
app.include_router(payments, prefix=api_v1_prefix)
app.include_router(auth_router, prefix=api_v1_prefix)
app.include_router(reviews, prefix=api_v1_prefix)
app.include_router(profile, prefix=api_v1_prefix)
app.include_router(categories, prefix=api_v1_prefix)
app.include_router(favorites, prefix=api_v1_prefix)

# Legacy routes (backward compatibility - no prefix)
app.include_router(search)
app.include_router(stores)
app.include_router(products)
app.include_router(owner)
app.include_router(admin)
app.include_router(orders)
app.include_router(cart)
app.include_router(chat)
app.include_router(shipping)
app.include_router(voice)
app.include_router(notifications)
app.include_router(tasks)
app.include_router(payments)
app.include_router(auth_router)
app.include_router(reviews)
app.include_router(profile)
app.include_router(categories)
app.include_router(favorites)


@app.get("/health")
async def health_check():
    """Health check endpoint with system status."""
    from src.cache import cache
    from src.vector_db import vector_db
    from src.config import config
    from sqlalchemy import text
    from src.db import async_session

    health_status = {
        "status": "ok",
        "version": "1.0.0",
        "environment": config.environment,
        "services": {
            "database": "unknown",
            "cache": "disabled",
            "vector_db": "disabled",
        },
        "timestamp": "2026-06-08T00:00:00Z",
    }

    # Test database connection
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        health_status["services"]["database"] = "ok"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["services"]["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    # Test cache
    if cache.client:
        try:
            await cache.client.ping()
            health_status["services"]["cache"] = "ok"
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            health_status["services"]["cache"] = f"error: {str(e)}"
            health_status["status"] = "degraded"

    # Test vector DB
    if vector_db.client:
        try:
            collections = vector_db.client.get_collections()
            health_status["services"]["vector_db"] = "ok"
        except Exception as e:
            logger.error(f"Vector DB health check failed: {e}")
            health_status["services"]["vector_db"] = f"error: {str(e)}"
            health_status["status"] = "degraded"

    return health_status
