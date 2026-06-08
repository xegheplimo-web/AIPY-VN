"""
Test configuration and fixtures for VietStore RAG API tests.
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from src.db import Base, get_db
from src.models.store import Store, Product, Category
from src.models.user import User
from src.models.order import Cart, CartItem, Order, OrderItem
from src.models.review import Review
import uuid
from datetime import datetime


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create async test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}, echo=False
)

# Create async session factory
AsyncTestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)

# Patch src.database BEFORE importing app so API routes get test session
import src.database as _db_module
_db_module.async_session = AsyncTestSessionLocal
_db_module.engine = test_engine

from src.main import app

# Patch database session BEFORE importing app (routes import async_session at module level)
import src.database as _db_module
_db_module.async_session = AsyncTestSessionLocal
_db_module.engine = test_engine


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database for each test."""
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session = AsyncTestSessionLocal()
    try:
        yield session
    finally:
        await session.close()
        # Drop all tables after test
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession):
    """Create a test client with database access."""

    async def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
async def sample_user(db_session: AsyncSession) -> User:
    """Create a sample user for testing."""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        phone="0123456789",
        password_hash="$2b$12$test_hash_for_testing",
        full_name="Test User",
        role="customer",
        is_verified=True,
        is_active=True,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def sample_category(db_session: AsyncSession) -> Category:
    """Create a sample category for testing."""
    category = Category(
        id=uuid.uuid4(),
        name="Grocery",
        slug="grocery",
        is_active=True,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    )
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)
    return category


@pytest.fixture
async def sample_store(db_session: AsyncSession, sample_category: Category) -> Store:
    """Create a sample store for testing."""
    store = Store(
        id=uuid.uuid4(),
        name="Test Store",
        address="123 Test Street",
        latitude=10.7743,
        longitude=106.7009,
        phone="0123456789",
        email="store@example.com",
        status="active",
        is_open_now=True,
        rating=4.5,
        total_reviews=10,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    )
    db_session.add(store)
    await db_session.commit()
    await db_session.refresh(store)
    return store


@pytest.fixture
async def sample_product(
    db_session: AsyncSession, sample_store: Store, sample_category: Category
) -> Product:
    """Create a sample product for testing."""
    product = Product(
        id=uuid.uuid4(),
        store_id=sample_store.id,
        name="Test Product",
        description="A test product",
        price=100.00,
        stock=10,
        unit="cái",
        category_id=sample_category.id,
        status="active",
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    return product


@pytest.fixture
async def sample_cart(
    db_session: AsyncSession, sample_user: User, sample_store: Store
) -> Cart:
    """Create a sample cart for testing."""
    cart = Cart(
        id=uuid.uuid4(),
        user_id=sample_user.id,
        store_id=sample_store.id,
        status="active",
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    )
    db_session.add(cart)
    await db_session.commit()
    await db_session.refresh(cart)
    return cart


@pytest.fixture
async def sample_cart_item(
    db_session: AsyncSession, sample_cart: Cart, sample_product: Product
) -> CartItem:
    """Create a sample cart item for testing."""
    cart_item = CartItem(
        id=uuid.uuid4(),
        cart_id=sample_cart.id,
        product_id=sample_product.id,
        quantity=2,
        unit_price=sample_product.price,
        subtotal=sample_product.price * 2,
        created_at=datetime.now().isoformat(),
    )
    db_session.add(cart_item)
    await db_session.commit()
    await db_session.refresh(cart_item)
    return cart_item


@pytest.fixture
async def sample_order(
    db_session: AsyncSession, sample_user: User, sample_store: Store
) -> Order:
    """Create a sample order for testing."""
    order = Order(
        id=uuid.uuid4(),
        order_number="ORD-2026-00001",
        user_id=sample_user.id,
        store_id=sample_store.id,
        delivery_method="delivery",
        delivery_address="123 Delivery Street",
        delivery_lat=10.7743,
        delivery_lng=106.7009,
        subtotal=200.00,
        shipping_fee=10.00,
        discount=0.00,
        total_amount=210.00,
        payment_method="cod",
        payment_status="pending",
        status="pending",
        created_at=datetime.now().isoformat(),
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)
    return order


@pytest.fixture
async def sample_review(
    db_session: AsyncSession, sample_store: Store, sample_user: User
) -> Review:
    """Create a sample review for testing."""
    review = Review(
        id=uuid.uuid4(),
        store_id=sample_store.id,
        user_id=sample_user.id,
        rating=5,
        comment="Great store!",
        created_at=datetime.now().isoformat(),
    )
    db_session.add(review)
    await db_session.commit()
    await db_session.refresh(review)
    return review


@pytest.fixture
def auth_headers():
    """Create mock authentication headers."""
    return {"Authorization": "Bearer mock_token_for_testing"}


@pytest.fixture
def admin_headers():
    """Create mock admin authentication headers."""
    return {"Authorization": "Bearer mock_admin_token_for_testing"}
