"""
Firebase Push Notification Service

Provides push notification functionality using Firebase Cloud Messaging (FCM).
"""

import logging
from typing import Any

try:
    from firebase_admin import credentials, messaging

    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

from src.config import config

logger = logging.getLogger(__name__)


class FirebaseNotificationService:
    """Service for Firebase Cloud Messaging (FCM) push notifications."""

    def __init__(self):
        """Initialize Firebase notification service."""
        self.app = None
        self._initialize_firebase()

    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK."""
        if not FIREBASE_AVAILABLE:
            logger.warning("firebase_admin not installed, push notifications disabled")
            return

        try:
            if not config.firebase.is_configured():
                logger.warning("Firebase not configured, push notifications disabled")
                return

            # Create credentials from config
            cred_dict = {
                "type": "service_account",
                "project_id": config.firebase.project_id,
                "private_key_id": config.firebase.private_key_id,
                "private_key": config.firebase.private_key.replace("\\n", "\n"),
                "client_email": config.firebase.client_email,
                "client_id": config.firebase.client_id,
                "auth_uri": config.firebase.auth_uri,
                "token_uri": config.firebase.token_uri,
                "auth_provider_x509_cert_url": config.firebase.auth_provider_x509_cert_url,
                "client_x509_cert_url": config.firebase.client_x509_cert_url,
            }

            credentials_dict = credentials.Certificate(cred_dict)
            self.app = messaging.initialize_app(credentials_dict)
            logger.info("Firebase initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            self.app = None

    def is_ready(self) -> bool:
        """Check if the service is ready."""
        return self.app is not None

    async def send_to_device(
        self, token: str, title: str, body: str, data: dict[str, Any] | None = None
    ) -> bool:
        """
        Send notification to a specific device.

        Args:
            token: FCM device token
            title: Notification title
            body: Notification body
            data: Optional custom data payload

        Returns:
            True if successful, False otherwise
        """
        if not self.is_ready():
            logger.warning("Firebase not ready, cannot send notification")
            return False

        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                token=token,
            )

            response = messaging.send(message)
            logger.info(f"Notification sent successfully: {response}")
            return True

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False

    async def send_to_topic(
        self, topic: str, title: str, body: str, data: dict[str, Any] | None = None
    ) -> bool:
        """
        Send notification to a topic.

        Args:
            topic: FCM topic name
            title: Notification title
            body: Notification body
            data: Optional custom data payload

        Returns:
            True if successful, False otherwise
        """
        if not self.is_ready():
            logger.warning("Firebase not ready, cannot send notification")
            return False

        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                topic=topic,
            )

            response = messaging.send(message)
            logger.info(f"Topic notification sent successfully: {response}")
            return True

        except Exception as e:
            logger.error(f"Failed to send topic notification: {e}")
            return False

    async def send_to_devices(
        self,
        tokens: list[str],
        title: str,
        body: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Send notification to multiple devices.

        Args:
            tokens: List of FCM device tokens
            title: Notification title
            body: Notification body
            data: Optional custom data payload

        Returns:
            Dictionary with success count and failure count
        """
        if not self.is_ready():
            logger.warning("Firebase not ready, cannot send notification")
            return {"success": 0, "failure": len(tokens)}

        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                tokens=tokens,
            )

            response = messaging.send_multicast(message)
            logger.info(
                f"Multicast notification sent: {response.success_count} success, {response.failure_count} failure"
            )

            return {
                "success": response.success_count,
                "failure": response.failure_count,
            }

        except Exception as e:
            logger.error(f"Failed to send multicast notification: {e}")
            return {"success": 0, "failure": len(tokens)}

    async def send_order_notification(
        self, token: str, order_id: str, status: str
    ) -> bool:
        """
        Send order status notification.

        Args:
            token: FCM device token
            order_id: Order ID
            status: Order status

        Returns:
            True if successful, False otherwise
        """
        title = "Cập nhật đơn hàng"
        body = f"Đơn hàng {order_id} đã chuyển sang trạng thái: {status}"
        data = {
            "type": "order_update",
            "order_id": order_id,
            "status": status,
        }

        return await self.send_to_device(token, title, body, data)

    async def send_promotion_notification(
        self, tokens: list[str], promotion_title: str, promotion_body: str
    ) -> dict[str, Any]:
        """
        Send promotion notification to multiple users.

        Args:
            tokens: List of FCM device tokens
            promotion_title: Promotion title
            promotion_body: Promotion body

        Returns:
            Dictionary with success count and failure count
        """
        data = {
            "type": "promotion",
        }

        return await self.send_to_devices(tokens, promotion_title, promotion_body, data)


# Global service instance
firebase_service = FirebaseNotificationService()


def get_firebase_service() -> FirebaseNotificationService:
    """Get the global Firebase service instance."""
    return firebase_service
