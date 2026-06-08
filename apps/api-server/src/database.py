import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/vietstore"
)
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

engine = create_async_engine(DATABASE_URL, echo=DEBUG)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# Import all models to ensure they're registered with Base
from src.models import (
    User,
    Address,
    Store,
    Product,
    Category,
    Cart,
    CartItem,
    Order,
    OrderItem,
    ProductVariant,
    Review,
    ChatMessage,
    Promotion,
    Report,
)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with async_session() as session:
        yield session
