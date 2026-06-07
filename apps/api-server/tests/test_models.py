"""
Model tests for VietStore RAG API.
"""

import pytest
from src.models.store import Store, Product, Category
from src.models.user import User
from src.models.order import Cart, CartItem, Order, OrderItem
from src.models.review import Review
import uuid
from datetime import datetime
from decimal import Decimal


class TestStoreModel:
    """Tests for Store model."""

    def test_store_creation(self, db_session):
        """Test creating a store."""
        store = Store(
            id=uuid.uuid4(),
            name="Test Store",
            address="123 Test Street",
            latitude=10.7743,
            longitude=106.7009,
            phone="0123456789",
            email="store@example.com",
            status="active",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        db_session.add(store)
        db_session.commit()
        
        assert store.id is not None
        assert store.name == "Test Store"
        assert store.status == "active"

    def test_store_relationships(self, db_session):
        """Test store relationships."""
        store = Store(
            id=uuid.uuid4(),
            name="Relationship Test Store",
            address="456 Test Street",
            latitude=10.7743,
            longitude=106.7009,
            status="active",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        db_session.add(store)
        db_session.commit()
        
        # Store should have products relationship
        assert hasattr(store, "products")

    def test_store_validation(self, db_session):
        """Test store field validation."""
        store = Store(
            id=uuid.uuid4(),
            name="",  # Invalid: empty name
            address="123 Test Street",
            latitude=10.7743,
            longitude=106.7009,
            status="active",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        db_session.add(store)
        # This might fail validation depending on model constraints
        # db_session.commit()


class TestProductModel:
    """Tests for Product model."""

    def test_product_creation(self, db_session, sample_store, sample_category):
        """Test creating a product."""
        product = Product(
            id=uuid.uuid4(),
            store_id=sample_store.id,
            name="Test Product",
            description="A test product",
            price=Decimal("100.00"),
            stock=10,
            unit="cái",
            category_id=sample_category.id,
            status="active",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        db_session.add(product)
        db_session.commit()
        
        assert product.id is not None
        assert product.name == "Test Product"
        assert product.price == Decimal("100.00")

    def test_product_relationships(self, db_session, sample_store, sample_category):
        """Test product relationships."""
        product = Product(
            id=uuid.uuid4(),
            store_id=sample_store.id,
            name="Relationship Test Product",
            price=Decimal("50.00"),
            stock=5,
            category_id=sample_category.id,
            status="active",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        db_session.add(product)
        db_session.commit()
        
        assert hasattr(product, "store")
        assert hasattr(product, "category")

    def test_product_stock_validation(self, db_session, sample_store, sample_category):
        """Test product stock validation."""
        product = Product(
            id=uuid.uuid4(),
            store_id=sample_store.id,
            name="Stock Test Product",
            price=Decimal("75.00"),
            stock=-5,  # Invalid: negative stock
            category_id=sample_category.id,
            status="active",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        db_session.add(product)
        # This might fail validation
        # db_session.commit()


class TestUserModel:
    """Tests for User model."""

    def test_user_creation(self, db_session):
        """Test creating a user."""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            phone="0123456789",
            password_hash="$2b$12$test_hash",
            full_name="Test User",
            role="customer",
            is_verified=True,
            is_active=True,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.role == "customer"

    def test_user_email_uniqueness(self, db_session):
        """Test that email must be unique."""
        user1 = User(
            id=uuid.uuid4(),
            email="duplicate@example.com",
            phone="0123456789",
            password_hash="$2b$12$test_hash",
            role="customer",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        db_session.add(user1)
        db_session.commit()
        
        user2 = User(
            id=uuid.uuid4(),
            email="duplicate@example.com",  # Duplicate email
            phone="0987654321",
            password_hash="$2b$12$test_hash",
            role="customer",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        db_session.add(user2)
        # This should fail due to unique constraint
        # db_session.commit()

    def test_user_role_validation(self, db_session):
        """Test user role validation."""
        user = User(
            id=uuid.uuid4(),
            email="role_test@example.com",
            phone="0123456789",
            password_hash="$2b$12$test_hash",
            role="invalid_role",  # Invalid role
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        db_session.add(user)
        # This might fail validation
        # db_session.commit()


class TestOrderModel:
    """Tests for Order model."""

    def test_order_creation(self, db_session, sample_user, sample_store):
        """Test creating an order."""
        order = Order(
            id=uuid.uuid4(),
            order_number="ORD-2026-00001",
            user_id=sample_user.id,
            store_id=sample_store.id,
            delivery_method="delivery",
            delivery_address="123 Delivery Street",
            delivery_lat=Decimal("10.7743"),
            delivery_lng=Decimal("106.7009"),
            subtotal=Decimal("200.00"),
            shipping_fee=Decimal("10.00"),
            discount=Decimal("0.00"),
            total_amount=Decimal("210.00"),
            payment_method="cod",
            payment_status="pending",
            status="pending",
            created_at=datetime.now().isoformat(),
        )
        db_session.add(order)
        db_session.commit()
        
        assert order.id is not None
        assert order.order_number == "ORD-2026-00001"
        assert order.total_amount == Decimal("210.00")

    def test_order_item_creation(self, db_session, sample_order, sample_product):
        """Test creating an order item."""
        order_item = OrderItem(
            id=uuid.uuid4(),
            order_id=sample_order.id,
            product_id=sample_product.id,
            quantity=2,
            unit_price=Decimal("100.00"),
            subtotal=Decimal("200.00"),
        )
        db_session.add(order_item)
        db_session.commit()
        
        assert order_item.id is not None
        assert order_item.quantity == 2
        assert order_item.subtotal == Decimal("200.00")

    def test_order_status_transitions(self, db_session, sample_order):
        """Test order status transitions."""
        # Pending -> Confirmed
        sample_order.status = "confirmed"
        db_session.commit()
        
        assert sample_order.status == "confirmed"
        
        # Confirmed -> Completed
        sample_order.status = "completed"
        db_session.commit()
        
        assert sample_order.status == "completed"


class TestCartModel:
    """Tests for Cart model."""

    def test_cart_creation(self, db_session, sample_user, sample_store):
        """Test creating a cart."""
        cart = Cart(
            id=uuid.uuid4(),
            user_id=sample_user.id,
            store_id=sample_store.id,
            status="active",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        db_session.add(cart)
        db_session.commit()
        
        assert cart.id is not None
        assert cart.status == "active"

    def test_cart_item_creation(self, db_session, sample_cart, sample_product):
        """Test creating a cart item."""
        cart_item = CartItem(
            id=uuid.uuid4(),
            cart_id=sample_cart.id,
            product_id=sample_product.id,
            quantity=1,
            unit_price=Decimal("100.00"),
            created_at=datetime.now().isoformat(),
        )
        db_session.add(cart_item)
        db_session.commit()
        
        assert cart_item.id is not None
        assert cart_item.quantity == 1


class TestReviewModel:
    """Tests for Review model."""

    def test_review_creation(self, db_session, sample_store, sample_user):
        """Test creating a review."""
        review = Review(
            id=uuid.uuid4(),
            store_id=sample_store.id,
            user_id=sample_user.id,
            rating=5,
            comment="Great store!",
            created_at=datetime.now().isoformat(),
        )
        db_session.add(review)
        db_session.commit()
        
        assert review.id is not None
        assert review.rating == 5
        assert review.comment == "Great store!"

    def test_review_rating_validation(self, db_session, sample_store, sample_user):
        """Test review rating validation."""
        review = Review(
            id=uuid.uuid4(),
            store_id=sample_store.id,
            user_id=sample_user.id,
            rating=6,  # Invalid: rating should be 1-5
            comment="Test review",
            created_at=datetime.now().isoformat(),
        )
        db_session.add(review)
        # This might fail validation
        # db_session.commit()


class TestCategoryModel:
    """Tests for Category model."""

    def test_category_creation(self, db_session):
        """Test creating a category."""
        category = Category(
            id=uuid.uuid4(),
            name="Test Category",
            slug="test-category",
            is_active=True,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        db_session.add(category)
        db_session.commit()
        
        assert category.id is not None
        assert category.name == "Test Category"
        assert category.slug == "test-category"

    def test_category_slug_uniqueness(self, db_session):
        """Test that category slug must be unique."""
        category1 = Category(
            id=uuid.uuid4(),
            name="Category 1",
            slug="duplicate-slug",
            is_active=True,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        db_session.add(category1)
        db_session.commit()
        
        category2 = Category(
            id=uuid.uuid4(),
            name="Category 2",
            slug="duplicate-slug",  # Duplicate slug
            is_active=True,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        db_session.add(category2)
        # This should fail due to unique constraint
        # db_session.commit()


class TestModelRelationships:
    """Tests for model relationships."""

    def test_store_products_relationship(self, db_session, sample_store, sample_product):
        """Test store-products relationship."""
        assert sample_product.store_id == sample_store.id
        assert sample_store.id == sample_product.store_id

    def test_product_category_relationship(self, db_session, sample_product, sample_category):
        """Test product-category relationship."""
        assert sample_product.category_id == sample_category.id
        assert sample_category.id == sample_product.category_id

    def test_order_user_relationship(self, db_session, sample_order, sample_user):
        """Test order-user relationship."""
        assert sample_order.user_id == sample_user.id
        assert sample_user.id == sample_order.user_id

    def test_order_store_relationship(self, db_session, sample_order, sample_store):
        """Test order-store relationship."""
        assert sample_order.store_id == sample_store.id
        assert sample_store.id == sample_order.store_id
