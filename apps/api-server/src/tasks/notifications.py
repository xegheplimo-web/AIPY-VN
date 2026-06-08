"""
Notification Tasks

Background tasks for sending push notifications.
"""

import logging

from src.celery_app import celery_app
from src.services.firebase import get_firebase_service

logger = logging.getLogger(__name__)


@celery_app.task(
    name="src.tasks.notifications.send_push_notification",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_push_notification(self, token: str, title: str, body: str, data: dict = None):
    """
    Send a push notification to a device.

    Args:
        token: FCM device token
        title: Notification title
        body: Notification body
        data: Optional custom data

    Returns:
        True if successful, False otherwise
    """
    try:
        firebase_service = get_firebase_service()

        if not firebase_service.is_ready():
            logger.warning("Firebase not ready, cannot send notification")
            return False

        result = firebase_service.send_to_device(token, title, body, data)
        logger.info(f"Push notification sent to {token[:20]}...")

        return result

    except Exception as e:
        logger.error(f"Failed to send push notification: {e}")
        raise self.retry(exc=e, countdown=2**self.request.retries)


@celery_app.task(
    name="src.tasks.notifications.send_order_notification", bind=True, max_retries=3
)
def send_order_notification(self, token: str, order_id: str, status: str):
    """
    Send order status notification.

    Args:
        token: FCM device token
        order_id: Order ID
        status: Order status

    Returns:
        True if successful
    """
    try:
        firebase_service = get_firebase_service()

        if not firebase_service.is_ready():
            logger.warning("Firebase not ready, cannot send order notification")
            return False

        result = firebase_service.send_order_notification(token, order_id, status)
        logger.info(f"Order notification sent for order {order_id}")

        return result

    except Exception as e:
        logger.error(f"Failed to send order notification: {e}")
        raise self.retry(exc=e, countdown=2**self.request.retries)


@celery_app.task(
    name="src.tasks.notifications.send_promotion_notification", bind=True, max_retries=3
)
def send_promotion_notification(
    self, tokens: list, promotion_title: str, promotion_body: str
):
    """
    Send promotion notification to multiple users.

    Args:
        tokens: List of FCM device tokens
        promotion_title: Promotion title
        promotion_body: Promotion body

    Returns:
        Dictionary with success/failure counts
    """
    try:
        firebase_service = get_firebase_service()

        if not firebase_service.is_ready():
            logger.warning("Firebase not ready, cannot send promotion notification")
            return {"success": 0, "failure": len(tokens)}

        result = firebase_service.send_promotion_notification(
            tokens, promotion_title, promotion_body
        )
        logger.info(f"Promotion notification sent: {result}")

        return result

    except Exception as e:
        logger.error(f"Failed to send promotion notification: {e}")
        raise self.retry(exc=e, countdown=2**self.request.retries)


@celery_app.task(
    name="src.tasks.notifications.send_bulk_notifications", bind=True, max_retries=3
)
def send_bulk_notifications(
    self, user_ids: list, title: str, body: str, data: dict = None
):
    """
    Send bulk notifications to multiple users.

    Args:
        user_ids: List of user IDs
        title: Notification title
        body: Notification body
        data: Optional custom data

    Returns:
        Dictionary with success/failure counts
    """
    try:
        # Note: In a real implementation, you would need to handle the async database calls
        # differently in Celery tasks. For now, this is a simplified version.
        logger.warning(
            "Bulk notification task requires async database handling - not implemented yet"
        )
        return {"success": 0, "failure": len(user_ids)}

    except Exception as e:
        logger.error(f"Failed to send bulk notification: {e}")
        raise self.retry(exc=e, countdown=2**self.request.retries)
