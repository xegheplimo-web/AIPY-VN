"""
Notification API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from src.middleware.auth_middleware import require_auth
from src.models.user import User
from src.services.notifications import (
    notification_service,
    NotificationType,
    NotificationPriority,
)

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("")
async def get_notifications(
    unread_only: bool = Query(False, description="Only return unread notifications"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of notifications"),
    current_user: User = Depends(require_auth),
):
    """
    Get notifications for the current user
    
    - Returns list of notifications
    - Can filter by unread status
    - Supports pagination with limit
    """
    notifications = await notification_service.get_user_notifications(
        user_id=str(current_user.id),
        unread_only=unread_only,
        limit=limit,
    )
    
    return {
        "notifications": [n.to_dict() for n in notifications],
        "total": len(notifications),
    }


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(require_auth),
):
    """
    Get count of unread notifications
    """
    count = await notification_service.get_unread_count(str(current_user.id))
    
    return {"unread_count": count}


@router.post("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    current_user: User = Depends(require_auth),
):
    """
    Mark a notification as read
    """
    success = await notification_service.mark_as_read(
        user_id=str(current_user.id),
        notification_id=notification_id,
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"message": "Notification marked as read"}


@router.post("/read-all")
async def mark_all_as_read(
    current_user: User = Depends(require_auth),
):
    """
    Mark all notifications as read
    """
    count = await notification_service.mark_all_as_read(str(current_user.id))
    
    return {"message": f"Marked {count} notifications as read"}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(require_auth),
):
    """
    Delete a notification
    """
    success = await notification_service.delete_notification(
        user_id=str(current_user.id),
        notification_id=notification_id,
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"message": "Notification deleted"}


# Admin-only endpoints for creating notifications
@router.post("/create")
async def create_notification(
    user_id: str,
    type: NotificationType,
    title: str,
    message: str,
    priority: NotificationPriority = NotificationPriority.MEDIUM,
    data: Optional[dict] = None,
    current_user: User = Depends(require_auth),
):
    """
    Create a notification (admin only)
    
    - Requires admin role
    - Creates notification for specified user
    - Sends to WebSocket if user is connected
    """
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    notification = await notification_service.create_notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        priority=priority,
        data=data,
    )
    
    return notification.to_dict()
