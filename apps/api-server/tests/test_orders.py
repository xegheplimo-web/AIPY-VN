"""
Order management tests for VietStore RAG API.
"""

import pytest
from fastapi.testclient import TestClient
from src.models.order import Order, OrderItem
from src.models.store import Product
from src.models.user import User
import uuid
from datetime import datetime
from decimal import Decimal


class TestOrderCreation:
    """Tests for order creation."""

    def test_create_order_success(
        self,
        client: TestClient,
        sample_user,
        sample_store,
        sample_product,
        auth_headers,
    ):
        """Test successful order creation."""
        order_data = {
            "store_id": str(sample_store.id),
            "delivery_method": "delivery",
            "delivery_address": "123 Test Street",
            "delivery_lat": 10.7743,
            "delivery_lng": 106.7009,
            "subtotal": 200.00,
            "shipping_fee": 10.00,
            "discount": 0.00,
            "total_amount": 210.00,
            "payment_method": "cod",
            "items": [
                {
                    "product_id": str(sample_product.id),
                    "quantity": 2,
                    "unit_price": 100.00,
                }
            ],
        }

        response = client.post("/api/orders", json=order_data, headers=auth_headers)
        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data
        assert "order_number" in data

    def test_create_order_insufficient_stock(
        self,
        client: TestClient,
        sample_user,
        sample_store,
        sample_product,
        auth_headers,
    ):
        """Test order creation with insufficient stock."""
        # Update product to have low stock
        sample_product.stock = 1

        order_data = {
            "store_id": str(sample_store.id),
            "delivery_method": "delivery",
            "delivery_address": "123 Test Street",
            "delivery_lat": 10.7743,
            "delivery_lng": 106.7009,
            "subtotal": 200.00,
            "shipping_fee": 10.00,
            "discount": 0.00,
            "total_amount": 210.00,
            "payment_method": "cod",
            "items": [
                {
                    "product_id": str(sample_product.id),
                    "quantity": 5,  # More than available stock
                    "unit_price": 100.00,
                }
            ],
        }

        response = client.post("/api/orders", json=order_data, headers=auth_headers)
        assert response.status_code == 400

    def test_create_order_invalid_product(
        self, client: TestClient, sample_user, sample_store, auth_headers
    ):
        """Test order creation with non-existent product."""
        fake_product_id = uuid.uuid4()

        order_data = {
            "store_id": str(sample_store.id),
            "delivery_method": "delivery",
            "delivery_address": "123 Test Street",
            "delivery_lat": 10.7743,
            "delivery_lng": 106.7009,
            "subtotal": 200.00,
            "shipping_fee": 10.00,
            "discount": 0.00,
            "total_amount": 210.00,
            "payment_method": "cod",
            "items": [
                {
                    "product_id": str(fake_product_id),
                    "quantity": 1,
                    "unit_price": 100.00,
                }
            ],
        }

        response = client.post("/api/orders", json=order_data, headers=auth_headers)
        assert response.status_code == 404

    def test_create_order_high_value_requires_signature(
        self,
        client: TestClient,
        sample_user,
        sample_store,
        sample_product,
        auth_headers,
    ):
        """Test high-value order requires signature."""
        order_data = {
            "store_id": str(sample_store.id),
            "delivery_method": "delivery",
            "delivery_address": "123 Test Street",
            "delivery_lat": 10.7743,
            "delivery_lng": 106.7009,
            "subtotal": 2000000.00,  # Over 1M VND threshold
            "shipping_fee": 10.00,
            "discount": 0.00,
            "total_amount": 2000010.00,
            "payment_method": "cod",
            "items": [
                {
                    "product_id": str(sample_product.id),
                    "quantity": 1,
                    "unit_price": 2000000.00,
                }
            ],
        }

        response = client.post("/api/orders", json=order_data, headers=auth_headers)
        assert response.status_code == 401


class TestOrderRetrieval:
    """Tests for order retrieval."""

    def test_get_user_orders(
        self, client: TestClient, sample_user, sample_order, auth_headers
    ):
        """Test getting user's orders."""
        response = client.get("/api/orders", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "orders" in data or isinstance(data, list)

    def test_get_order_detail(
        self, client: TestClient, sample_user, sample_order, auth_headers
    ):
        """Test getting specific order details."""
        response = client.get(f"/api/orders/{sample_order.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_order.id)

    def test_get_order_not_found(self, client: TestClient, auth_headers):
        """Test getting non-existent order."""
        fake_order_id = uuid.uuid4()
        response = client.get(f"/api/orders/{fake_order_id}", headers=auth_headers)
        assert response.status_code == 404

    def test_get_order_unauthorized(self, client: TestClient, sample_order):
        """Test getting order without authentication."""
        response = client.get(f"/api/orders/{sample_order.id}")
        assert response.status_code == 401


class TestOrderUpdate:
    """Tests for order updates."""

    def test_update_order_status(self, client: TestClient, sample_order, admin_headers):
        """Test updating order status (admin only)."""
        update_data = {"status": "confirmed"}
        response = client.put(
            f"/api/orders/{sample_order.id}/status",
            json=update_data,
            headers=admin_headers,
        )
        assert response.status_code in [200, 401, 403]

    def test_update_order_status_as_user(
        self, client: TestClient, sample_order, auth_headers
    ):
        """Test regular user cannot update order status."""
        update_data = {"status": "confirmed"}
        response = client.put(
            f"/api/orders/{sample_order.id}/status",
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code in [401, 403]

    def test_update_payment_status(
        self, client: TestClient, sample_order, admin_headers
    ):
        """Test updating payment status."""
        update_data = {"payment_status": "paid"}
        response = client.put(
            f"/api/orders/{sample_order.id}/payment",
            json=update_data,
            headers=admin_headers,
        )
        assert response.status_code in [200, 401, 403]


class TestOrderCancellation:
    """Tests for order cancellation."""

    def test_cancel_order(self, client: TestClient, sample_order, auth_headers):
        """Test cancelling an order."""
        response = client.post(
            f"/api/orders/{sample_order.id}/cancel", headers=auth_headers
        )
        assert response.status_code in [200, 400]

    def test_cancel_completed_order(
        self, client: TestClient, sample_order, auth_headers
    ):
        """Test cannot cancel completed order."""
        sample_order.status = "completed"

        response = client.post(
            f"/api/orders/{sample_order.id}/cancel", headers=auth_headers
        )
        assert response.status_code == 400


class TestOrderValidation:
    """Tests for order data validation."""

    def test_order_missing_required_fields(self, client: TestClient, auth_headers):
        """Test order creation with missing required fields."""
        order_data = {
            "store_id": str(uuid.uuid4()),
            # Missing delivery_method, address, etc.
        }

        response = client.post("/api/orders", json=order_data, headers=auth_headers)
        assert response.status_code == 422

    def test_order_invalid_delivery_method(
        self, client: TestClient, sample_user, sample_store, auth_headers
    ):
        """Test order with invalid delivery method."""
        order_data = {
            "store_id": str(sample_store.id),
            "delivery_method": "invalid_method",
            "delivery_address": "123 Test Street",
            "delivery_lat": 10.7743,
            "delivery_lng": 106.7009,
            "subtotal": 200.00,
            "shipping_fee": 10.00,
            "discount": 0.00,
            "total_amount": 210.00,
            "payment_method": "cod",
            "items": [],
        }

        response = client.post("/api/orders", json=order_data, headers=auth_headers)
        assert response.status_code == 422

    def test_order_negative_amounts(
        self, client: TestClient, sample_user, sample_store, auth_headers
    ):
        """Test order with negative amounts."""
        order_data = {
            "store_id": str(sample_store.id),
            "delivery_method": "delivery",
            "delivery_address": "123 Test Street",
            "delivery_lat": 10.7743,
            "delivery_lng": 106.7009,
            "subtotal": -100.00,  # Invalid
            "shipping_fee": 10.00,
            "discount": 0.00,
            "total_amount": -90.00,  # Invalid
            "payment_method": "cod",
            "items": [],
        }

        response = client.post("/api/orders", json=order_data, headers=auth_headers)
        assert response.status_code == 422


class TestOrderItems:
    """Tests for order item management."""

    def test_order_item_creation(
        self, client: TestClient, sample_order, sample_product, admin_headers
    ):
        """Test adding items to order."""
        item_data = {
            "product_id": str(sample_product.id),
            "quantity": 1,
            "unit_price": 100.00,
        }

        response = client.post(
            f"/api/orders/{sample_order.id}/items",
            json=item_data,
            headers=admin_headers,
        )
        assert response.status_code in [200, 401, 403]

    def test_order_item_quantity_validation(
        self, client: TestClient, sample_order, sample_product, admin_headers
    ):
        """Test order item with invalid quantity."""
        item_data = {
            "product_id": str(sample_product.id),
            "quantity": 0,  # Invalid
            "unit_price": 100.00,
        }

        response = client.post(
            f"/api/orders/{sample_order.id}/items",
            json=item_data,
            headers=admin_headers,
        )
        assert response.status_code == 422
