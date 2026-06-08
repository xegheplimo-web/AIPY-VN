"""
Real-time notification service
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


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


class NotificationService:
    """Service for managing real-time notifications"""
    
    def __init__(self):
        # In-memory storage (in production, use Redis or database)
        self._notifications: Dict[str, List[Notification]] = {}
        self._user_connections: Dict[str, List] = {}  # user_id -> list of WebSocket connections
    
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
        Create a new notification
        
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
        import uuid
        
        notification = Notification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            priority=priority,
            data=data,
        )
        
        # Store notification
        if user_id not in self._notifications:
            self._notifications[user_id] = []
        
        self._notifications[user_id].insert(0, notification)
        
        # Keep only last 100 notifications per user
        if len(self._notifications[user_id]) > 100:
            self._notifications[user_id] = self._notifications[user_id][:100]
        
        # Send to connected WebSocket clients
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
        Get notifications for a user
        
        Args:
            user_id: ID of the user
            unread_only: Only return unread notifications
            limit: Maximum number of notifications to return
        
        Returns:
            List of notifications
        """
        notifications = self._notifications.get(user_id, [])
        
        if unread_only:
            notifications = [n for n in notifications if not n.read]
        
        return notifications[:limit]
    
    async def mark_as_read(self, user_id: str, notification_id: str) -> bool:
        """
        Mark a notification as read
        
        Args:
            user_id: ID of the user
            notification_id: ID of the notification
        
        Returns:
            True if successful, False otherwise
        """
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
        Mark all notifications as read for a user
        
        Args:
            user_id: ID of the user
        
        Returns:
            Number of notifications marked as read
        """
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
        Delete a notification
        
        Args:
            user_id: ID of the user
            notification_id: ID of the notification
        
        Returns:
            True if successful, False otherwise
        """
        if user_id not in self._notifications:
            return False
        
        for i, notification in enumerate(self._notifications[user_id]):
            if notification.id == notification_id:
                self._notifications[user_id].pop(i)
                logger.info(f"Deleted notification {notification_id} for user {user_id}")
                return True
        
        return False
    
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
        for websocket in self._user_connections[user_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send notification to user {user_id}: {e}")
    
    async def get_unread_count(self, user_id: str) -> int:
        """
        Get count of unread notifications for a user
        
        Args:
            user_id: ID of the user
        
        Returns:
            Number of unread notifications
        """
        if user_id not in self._notifications:
            return 0
        
        return sum(1 for n in self._notifications[user_id] if not n.read)


# Global notification service instance
notification_service = NotificationService()
