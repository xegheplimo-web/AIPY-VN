"""
Celery Configuration

Background task queue configuration using Redis as broker.
"""

from celery import Celery
from src.config import config

# Create Celery app
celery_app = Celery(
    "vietstore",
    broker=config.redis.url,
    backend=config.redis.url,
    include=[
        "src.tasks.email",
        "src.tasks.notifications",
        "src.tasks.orders",
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Task result expiration (1 day)
celery_app.conf.result_expires = 86400

# Task routing (optional - for different queues)
celery_app.conf.task_routes = {
    "src.tasks.email.send_email": {"queue": "email"},
    "src.tasks.notifications.send_push_notification": {"queue": "notifications"},
    "src.tasks.orders.process_order": {"queue": "orders"},
}

# Retry settings
celery_app.conf.task_default_retry_delay = 60  # 1 minute
celery_app.conf.task_max_retries = 3
celery_app.conf.task_acks_late = True
