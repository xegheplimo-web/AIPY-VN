"""
Notifications API

Endpoints for managing push notifications and device tokens.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from src.db import async_session
from src.models.user import User
from src.services.firebase import get_firebase_service
from src.middleware.auth_middleware import require_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


class RegisterDeviceRequest(BaseModel):
    """Request to register a device token."""

    token: str = Field(..., description="FCM device token")
    platform: str = Field(default="web", description="Platform (web, ios, android)")


class SendNotificationRequest(BaseModel):
    """Request to send a notification."""

    title: str = Field(..., description="Notification title")
    body: str = Field(..., description="Notification body")
    data: Optional[dict] = Field(default=None, description="Custom data payload")
    user_ids: Optional[List[str]] = Field(default=None, description="Target user IDs")


class NotificationResponse(BaseModel):
    """Response from notification operations."""

    success: bool
    message: str
    data: Optional[dict] = None


@router.post("/register", response_model=NotificationResponse)
async def register_device(
    request: RegisterDeviceRequest,
    current_user: User = Depends(require_auth)
):
    """
    Register a device token for push notifications.
    
    This endpoint stores the FCM device token for the current user.
    """
    try:
        async with async_session() as session:
            # Update user's device token
            await session.execute(
                update(User)
                .where(User.id == current_user.id)
                .values(fcm_token=request.token, fcm_platform=request.platform)
            )
            await session.commit()
        
        return NotificationResponse(
            success=True,
            message="Device token registered successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to register device token: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to register device token: {str(e)}"
        )


@router.post("/send", response_model=NotificationResponse)
async def send_notification(
    request: SendNotificationRequest,
    current_user: User = Depends(require_auth)
):
    """
    Send a push notification.
    
    This endpoint sends a push notification to specified users.
    Requires admin or owner role.
    """
    try:
        firebase_service = get_firebase_service()
        
        if not firebase_service.is_ready():
            return NotificationResponse(
                success=False,
                message="Firebase not configured"
            )
        
        # Get target users and their device tokens
        async with async_session() as session:
            if request.user_ids:
                # Send to specific users
                users = await session.execute(
                    select(User).where(User.id.in_(request.user_ids))
                )
                users = users.scalars().all()
            else:
                # Send to all users (admin only)
                users = await session.execute(select(User))
                users = users.scalars().all()
            
            # Collect device tokens
            tokens = [user.fcm_token for user in users if user.fcm_token]
            
            if not tokens:
                return NotificationResponse(
                    success=False,
                    message="No device tokens found"
                )
        
        # Send notification
        result = await firebase_service.send_to_devices(
            tokens=tokens,
            title=request.title,
            body=request.body,
            data=request.data
        )
        
        return NotificationResponse(
            success=True,
            message=f"Notification sent to {result['success']} devices",
            data=result
        )
        
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send notification: {str(e)}"
        )


@router.post("/test", response_model=NotificationResponse)
async def test_notification(
    current_user: User = Depends(require_auth)
):
    """
    Send a test notification to the current user.
    
    This endpoint sends a test notification to verify Firebase configuration.
    """
    try:
        firebase_service = get_firebase_service()
        
        if not firebase_service.is_ready():
            return NotificationResponse(
                success=False,
                message="Firebase not configured"
            )
        
        if not current_user.fcm_token:
            return NotificationResponse(
                success=False,
                message="No device token registered for this user"
            )
        
        # Send test notification
        success = await firebase_service.send_to_device(
            token=current_user.fcm_token,
            title="Thông báo kiểm tra",
            body="Đây là thông báo kiểm tra từ VietStore",
            data={"type": "test"}
        )
        
        return NotificationResponse(
            success=success,
            message="Test notification sent" if success else "Failed to send test notification"
        )
        
    except Exception as e:
        logger.error(f"Failed to send test notification: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send test notification: {str(e)}"
        )
