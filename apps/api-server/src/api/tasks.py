"""
Background Tasks API

Endpoints for managing and triggering background tasks.
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from src.celery_app import celery_app
from src.tasks.email import send_welcome_email
from src.tasks.orders import process_order

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskResponse(BaseModel):
    """Response from task operations."""

    success: bool
    message: str
    task_id: str = None


class SendEmailRequest(BaseModel):
    """Request to send an email."""

    to_email: str = Field(..., description="Recipient email")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body")


class ProcessOrderRequest(BaseModel):
    """Request to process an order."""

    order_id: str = Field(..., description="Order ID")


@router.post("/email/send", response_model=TaskResponse)
async def send_email_task(request: SendEmailRequest):
    """
    Send an email in the background.
    
    This endpoint triggers a background task to send an email.
    """
    try:
        from src.tasks.email import send_email
        
        task = send_email.delay(request.to_email, request.subject, request.body)
        
        return TaskResponse(
            success=True,
            message="Email task queued",
            task_id=task.id
        )
        
    except Exception as e:
        logger.error(f"Failed to queue email task: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue email task: {str(e)}"
        )


@router.post("/email/welcome", response_model=TaskResponse)
async def send_welcome_email_task(email: str, name: str):
    """
    Send welcome email to a new user.
    
    This endpoint triggers a background task to send a welcome email.
    """
    try:
        task = send_welcome_email.delay(email, name)
        
        return TaskResponse(
            success=True,
            message="Welcome email task queued",
            task_id=task.id
        )
        
    except Exception as e:
        logger.error(f"Failed to queue welcome email task: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue welcome email task: {str(e)}"
        )


@router.post("/order/process", response_model=TaskResponse)
async def process_order_task(request: ProcessOrderRequest):
    """
    Process an order in the background.
    
    This endpoint triggers a background task to process an order.
    """
    try:
        task = process_order.delay(request.order_id)
        
        return TaskResponse(
            success=True,
            message="Order processing task queued",
            task_id=task.id
        )
        
    except Exception as e:
        logger.error(f"Failed to queue order processing task: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue order processing task: {str(e)}"
        )


@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Get the status of a background task.
    
    Args:
        task_id: Celery task ID
    
    Returns:
        Task status information
    """
    try:
        task = celery_app.AsyncResult(task_id)
        
        return {
            "task_id": task_id,
            "status": task.status,
            "result": task.result if task.ready() else None,
        }
        
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task status: {str(e)}"
        )


@router.post("/test")
async def test_background_task():
    """
    Test background task execution.
    
    This endpoint triggers a simple test task to verify Celery is working.
    """
    try:
        from src.tasks.email import send_email
        
        task = send_email.delay(
            "test@example.com",
            "Test Email",
            "This is a test email from VietStore background task system."
        )
        
        return TaskResponse(
            success=True,
            message="Test task queued successfully",
            task_id=task.id
        )
        
    except Exception as e:
        logger.error(f"Failed to queue test task: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue test task: {str(e)}"
        )
