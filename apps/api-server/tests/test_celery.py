"""
Tests for Celery Background Tasks
"""

import pytest
from src.celery_app import celery_app
from src.tasks.email import send_email
from src.tasks.notifications import send_push_notification
from src.tasks.orders import process_order


class TestCeleryTasks:
    """Tests for Celery background tasks."""

    def test_celery_app_initialization(self):
        """Test Celery app initializes correctly."""
        assert celery_app is not None
        assert celery_app.main == "vietstore"
        assert celery_app.conf.broker is not None
        assert celery_app.conf.backend is not None

    def test_send_email_task(self):
        """Test email task can be queued."""
        task = send_email.delay(
            "test@example.com",
            "Test Subject",
            "Test Body"
        )
        assert task.id is not None
        assert task.status in ["PENDING", "SUCCESS", "FAILURE"]

    def test_send_push_notification_task(self):
        """Test push notification task can be queued."""
        task = send_push_notification.delay(
            "test_token",
            "Test Title",
            "Test Body"
        )
        assert task.id is not None
        assert task.status in ["PENDING", "SUCCESS", "FAILURE"]

    def test_process_order_task(self):
        """Test order processing task can be queued."""
        task = process_order.delay("test-order-id")
        assert task.id is not None
        assert task.status in ["PENDING", "SUCCESS", "FAILURE"]


def test_celery_config():
    """Test Celery configuration."""
    assert celery_app.conf.task_serializer == "json"
    assert celery_app.conf.accept_content == ["json"]
    assert celery_app.conf.result_serializer == "json"
    assert celery_app.conf.enable_utc is True
