"""
Real-time notification service with Redis-backed storage.

Notifications are stored as JSON entries in Redis lists with a 30-day TTL.
If Redis is unavailable the service falls back to in-memory storage
while keeping the same class interface.
"""

import json
import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

# Redis key constants
NOTIFICATION_KEY_PREFIX = "notifications:"
NOTIFICATION_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 days
MAX_NOTIFICATIONS_PER_USER = 100

# Lazy-loaded Redis client
_redis_client = None


def _get_redis_client():
    """
    Lazily resolve the async Redis client from the project's cache module.

    Returns the underlying ``redis.asyncio.Redis`` instance or ``None`` if
    Redis is not available.
    """
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    try:
        from src.cache import cache
        client = cache.client
        if client is not None:
            _redis_client = client
            return _redis_client
    except Exception as exc:
        logger.debug(f"Redis client not available from cache module: {exc}")

    return None


def _redis_key(user_id: str) -> str:
    """Return the Redis list key for a given user."""
    return f"{NOTIFICATION_KEY_PREFIX}{user_id}"


class NotificationType(str, Enum):
    """Notification types"""
    ORDER_CREATED = "order_created"
    ORDER_UPDATED = "order_updated"
    PAYMENT_RECEIVED = "payment_received"
    PRODUCT_OUT_OF_STOCK = "product_out_of_stock"
    STORE_VERIFIED = "store_verified"
    STORE_SUSPENDED = "store_suspended"
    USER_BANNED = "user_banned"
    REPORT_RESOLVED = "report_resolved"
    PROMOTION_STARTED = "promotion_started"
    PROMOTION_ENDED = "promotion_ended"
    SYSTEM_ALERT = "system_alert"


class NotificationPriority(str, Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Notification:
    """Notification model"""

    def __init__(
        self,
        id: str,
        user_id: str,
        type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        data: Optional[Dict[str, Any]] = None,
        read: bool = False,
        created_at: Optional[str] = None,
    ):
        self.id = id
        self.user_id = user_id
        self.type = type
        self.title = title
        self.message = message
        self.priority = priority
        self.data = data or {}
        self.read = read
        self.created_at = created_at or datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type.value,
            "title": self.title,
            "message": self.message,
            "priority": self.priority.value,
            "data": self.data,
            "read": self.read,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Notification":
        """Reconstruct a Notification from a dictionary."""
        return cls(
            id=data["id"],
            user_id=data["user_id"],
            type=NotificationType(data["type"]),
            title=data["title"],
            message=data["message"],
            priority=NotificationPriority(data.get("priority", "medium")),
            data=data.get("data", {}),
            read=data.get("read", False),
            created_at=data.get("created_at"),
        )

    def to_json(self) -> str:
        """Serialize to JSON string for Redis storage."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, raw: str) -> "Notification":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(raw))


class NotificationService:
    """
    Service for managing real-time notifications.

    Primary storage: Redis list at ``notifications:{user_id}``.
    Fallback: in-memory dict when Redis is unavailable.
    """

    def __init__(self):
        # In-memory fallback storage
        self._notifications: Dict[str, List[Notification]] = {}
        # WebSocket connection registry (always in-memory)
        self._user_connections: Dict[str, List] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _redis_push(self, user_id: str, notification: Notification) -> bool:
        """
        Push a notification to the user's Redis list.

        Returns True if the operation succeeded (Redis available), False
        if Redis was unavailable and the caller should fall back to
        in-memory storage.
        """
        client = _get_redis_client()
        if client is None:
            return False

        try:
            key = _redis_key(user_id)

            # LPUSH adds to the head of the list (newest first)
            await client.lpush(key, notification.to_json())

            # Trim to MAX_NOTIFICATIONS_PER_USER
            await client.ltrim(key, 0, MAX_NOTIFICATIONS_PER_USER - 1)

            # Set / refresh TTL
            await client.expire(key, NOTIFICATION_TTL_SECONDS)

            return True
        except Exception as exc:
            logger.warning(f"Redis push failed for user {user_id}: {exc}")
            return False

    async def _redis_get_range(
        self, user_id: str, start: int = 0, end: int = -1
    ) -> Optional[List[Notification]]:
        """
        Retrieve a range of notifications from Redis.

        Returns a list of Notification objects, or None if Redis is
        unavailable (signal to fall back to in-memory).
        """
        client = _get_redis_client()
        if client is None:
            return None

        try:
            key = _redis_key(user_id)
            raw_list = await client.lrange(key, start, end)
            notifications = [Notification.from_json(raw) for raw in raw_list]
            return notifications
        except Exception as exc:
            logger.warning(f"Redis get_range failed for user {user_id}: {exc}")
            return None

    async def _redis_replace_all(self, user_id: str, notifications: List[Notification]) -> bool:
        """
        Replace the entire notification list for a user in Redis.

        Used after bulk mutations (mark_all_read, delete).
        Returns True if Redis was used, False otherwise.
        """
        client = _get_redis_client()
        if client is None:
            return False

        try:
            key = _redis_key(user_id)

            # Delete existing list and repopulate
            await client.delete(key)

            if notifications:
                # Pipeline for efficiency
                pipe = client.pipeline()
                for n in notifications:
                    pipe.lpush(key, n.to_json())
                await pipe.execute()

                # Trim and set TTL
                await client.ltrim(key, 0, MAX_NOTIFICATIONS_PER_USER - 1)
                await client.expire(key, NOTIFICATION_TTL_SECONDS)

            return True
        except Exception as exc:
            logger.warning(f"Redis replace_all failed for user {user_id}: {exc}")
            return False

    # ------------------------------------------------------------------
    # In-memory fallback helpers
    # ------------------------------------------------------------------

    def _mem_store(self, user_id: str, notification: Notification) -> None:
        """Store a notification in the in-memory fallback dict."""
        if user_id not in self._notifications:
            self._notifications[user_id] = []
        self._notifications[user_id].insert(0, notification)
        # Keep only last 100
        if len(self._notifications[user_id]) > MAX_NOTIFICATIONS_PER_USER:
            self._notifications[user_id] = self._notifications[user_id][:MAX_NOTIFICATIONS_PER_USER]

    def _mem_get(self, user_id: str) -> List[Notification]:
        """Get notifications from the in-memory fallback dict."""
        return self._notifications.get(user_id, [])

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def create_notification(
        self,
        user_id: str,
        type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        data: Optional[Dict[str, Any]] = None,
    ) -> Notification:
        """
        Create a new notification.

        The notification is persisted to Redis first; if Redis is
        unavailable it is stored in-memory instead.

        Args:
            user_id: ID of the user to notify
            type: Type of notification
            title: Notification title
            message: Notification message
            priority: Notification priority
            data: Additional data for the notification

        Returns:
            Created notification
        """
        notification = Notification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            priority=priority,
            data=data,
        )

        # Try Redis first
        redis_ok = await self._redis_push(user_id, notification)
        if not redis_ok:
            # Fall back to in-memory
            self._mem_store(user_id, notification)

        # Push to connected WebSocket clients
        await self._send_to_user(user_id, notification)

        logger.info(f"Created notification for user {user_id}: {title}")
        return notification

    async def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
    ) -> List[Notification]:
        """
        Get notifications for a user.

        Args:
            user_id: ID of the user
            unread_only: Only return unread notifications
            limit: Maximum number of notifications to return

        Returns:
            List of notifications
        """
        # Try Redis first
        notifications = await self._redis_get_range(user_id, 0, limit - 1)
        if notifications is None:
            # Fall back to in-memory
            notifications = self._mem_get(user_id)[:limit]

        if unread_only:
            notifications = [n for n in notifications if not n.read]

        return notifications[:limit]

    async def mark_as_read(self, user_id: str, notification_id: str) -> bool:
        """
        Mark a notification as read.

        Args:
            user_id: ID of the user
            notification_id: ID of the notification

        Returns:
            True if successful, False otherwise
        """
        # Try Redis first
        notifications = await self._redis_get_range(user_id)
        if notifications is not None:
            found = False
            for n in notifications:
                if n.id == notification_id:
                    n.read = True
                    found = True
                    break
            if found:
                await self._redis_replace_all(user_id, notifications)
                logger.info(f"Marked notification {notification_id} as read for user {user_id}")
                return True
            return False

        # In-memory fallback
        if user_id not in self._notifications:
            return False

        for notification in self._notifications[user_id]:
            if notification.id == notification_id:
                notification.read = True
                logger.info(f"Marked notification {notification_id} as read for user {user_id}")
                return True

        return False

    async def mark_all_as_read(self, user_id: str) -> int:
        """
        Mark all notifications as read for a user.

        Args:
            user_id: ID of the user

        Returns:
            Number of notifications marked as read
        """
        # Try Redis first
        notifications = await self._redis_get_range(user_id)
        if notifications is not None:
            count = 0
            for n in notifications:
                if not n.read:
                    n.read = True
                    count += 1
            if count > 0:
                await self._redis_replace_all(user_id, notifications)
            logger.info(f"Marked {count} notifications as read for user {user_id}")
            return count

        # In-memory fallback
        if user_id not in self._notifications:
            return 0

        count = 0
        for notification in self._notifications[user_id]:
            if not notification.read:
                notification.read = True
                count += 1

        logger.info(f"Marked {count} notifications as read for user {user_id}")
        return count

    async def delete_notification(self, user_id: str, notification_id: str) -> bool:
        """
        Delete a notification.

        Args:
            user_id: ID of the user
            notification_id: ID of the notification

        Returns:
            True if successful, False otherwise
        """
        # Try Redis first
        notifications = await self._redis_get_range(user_id)
        if notifications is not None:
            filtered = [n for n in notifications if n.id != notification_id]
            if len(filtered) < len(notifications):
                await self._redis_replace_all(user_id, filtered)
                logger.info(f"Deleted notification {notification_id} for user {user_id}")
                return True
            return False

        # In-memory fallback
        if user_id not in self._notifications:
            return False

        for i, notification in enumerate(self._notifications[user_id]):
            if notification.id == notification_id:
                self._notifications[user_id].pop(i)
                logger.info(f"Deleted notification {notification_id} for user {user_id}")
                return True

        return False

    async def get_unread_count(self, user_id: str) -> int:
        """
        Get count of unread notifications for a user.

        Args:
            user_id: ID of the user

        Returns:
            Number of unread notifications
        """
        # Try Redis first
        notifications = await self._redis_get_range(user_id)
        if notifications is not None:
            return sum(1 for n in notifications if not n.read)

        # In-memory fallback
        if user_id not in self._notifications:
            return 0

        return sum(1 for n in self._notifications[user_id] if not n.read)

    # ------------------------------------------------------------------
    # WebSocket connection management (always in-memory)
    # ------------------------------------------------------------------

    def register_connection(self, user_id: str, websocket):
        """
        Register a WebSocket connection for a user

        Args:
            user_id: ID of the user
            websocket: WebSocket connection
        """
        if user_id not in self._user_connections:
            self._user_connections[user_id] = []

        self._user_connections[user_id].append(websocket)
        logger.info(f"Registered WebSocket connection for user {user_id}")

    def unregister_connection(self, user_id: str, websocket):
        """
        Unregister a WebSocket connection for a user

        Args:
            user_id: ID of the user
            websocket: WebSocket connection
        """
        if user_id in self._user_connections:
            if websocket in self._user_connections[user_id]:
                self._user_connections[user_id].remove(websocket)

            # Clean up empty lists
            if not self._user_connections[user_id]:
                del self._user_connections[user_id]

        logger.info(f"Unregistered WebSocket connection for user {user_id}")

    async def _send_to_user(self, user_id: str, notification: Notification):
        """
        Send notification to user's WebSocket connections

        Args:
            user_id: ID of the user
            notification: Notification to send
        """
        if user_id not in self._user_connections:
            return

        message = {
            "type": "notification",
            "data": notification.to_dict(),
        }

        # Send to all connected clients for this user
        for websocket in list(self._user_connections[user_id]):
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send notification to user {user_id}: {e}")


# Global notification service instance
notification_service = NotificationService()
