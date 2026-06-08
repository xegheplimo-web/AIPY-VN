"""
Audit logging service for sensitive operations
"""

import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import Request
from sqlalchemy.dialects.postgresql import UUID

from src.database import async_session
from src.models.user import User

logger = logging.getLogger(__name__)


class AuditLogger:
    """Service for logging sensitive operations"""
    
    # Sensitive operations that require audit logging
    SENSITIVE_OPERATIONS = [
        "user_login",
        "user_logout",
        "user_register",
        "password_change",
        "password_reset",
        "order_create",
        "order_update",
        "order_cancel",
        "payment_process",
        "payment_refund",
        "store_create",
        "store_update",
        "store_delete",
        "product_create",
        "product_update",
        "product_delete",
        "promotion_create",
        "promotion_update",
        "promotion_delete",
        "user_role_change",
        "key_rotation",
        "admin_action",
    ]
    
    @staticmethod
    async def log_operation(
        operation: str,
        user_id: Optional[str],
        request: Optional[Request] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error_message: Optional[str] = None,
    ):
        """
        Log a sensitive operation
        
        Args:
            operation: Type of operation (e.g., "user_login", "order_create")
            user_id: ID of the user performing the operation
            request: FastAPI request object (for IP, user agent, etc.)
            details: Additional details about the operation
            status: Status of the operation ("success", "failed", "partial")
            error_message: Error message if operation failed
        """
        try:
            # Build audit log entry
            audit_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "operation": operation,
                "user_id": str(user_id) if user_id else None,
                "status": status,
                "details": details or {},
            }
            
            # Add request context if available
            if request:
                audit_entry["request"] = {
                    "ip": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent"),
                    "path": request.url.path,
                    "method": request.method,
                }
            
            # Add error message if failed
            if error_message:
                audit_entry["error"] = error_message
            
            # Log to structured logger
            logger.info(
                f"AUDIT: {operation}",
                extra={
                    "audit_log": audit_entry,
                    "user_id": user_id,
                    "operation": operation,
                    "status": status,
                }
            )
            
            # In production, also store in database
            # TODO: Create AuditLog model and store in database
            
        except Exception as e:
            logger.error(f"Failed to log audit entry: {e}", exc_info=True)
    
    @staticmethod
    async def log_login(user_id: str, request: Request, success: bool = True):
        """Log user login attempt"""
        await AuditLogger.log_operation(
            operation="user_login",
            user_id=user_id,
            request=request,
            status="success" if success else "failed",
            error_message=None if success else "Authentication failed",
        )
    
    @staticmethod
    async def log_logout(user_id: str, request: Request):
        """Log user logout"""
        await AuditLogger.log_operation(
            operation="user_logout",
            user_id=user_id,
            request=request,
            status="success",
        )
    
    @staticmethod
    async def log_order_create(
        user_id: str,
        order_id: str,
        amount: float,
        request: Request,
    ):
        """Log order creation"""
        await AuditLogger.log_operation(
            operation="order_create",
            user_id=user_id,
            request=request,
            details={
                "order_id": order_id,
                "amount": amount,
            },
            status="success",
        )
    
    @staticmethod
    async def log_payment_process(
        user_id: str,
        order_id: str,
        amount: float,
        payment_method: str,
        request: Request,
        success: bool = True,
    ):
        """Log payment processing"""
        await AuditLogger.log_operation(
            operation="payment_process",
            user_id=user_id,
            request=request,
            details={
                "order_id": order_id,
                "amount": amount,
                "payment_method": payment_method,
            },
            status="success" if success else "failed",
        )
    
    @staticmethod
    async def log_key_rotation(
        user_id: str,
        old_key_hash: str,
        new_key_hash: str,
        request: Request,
    ):
        """Log ECC key rotation"""
        await AuditLogger.log_operation(
            operation="key_rotation",
            user_id=user_id,
            request=request,
            details={
                "old_key_hash": old_key_hash,
                "new_key_hash": new_key_hash,
            },
            status="success",
        )
    
    @staticmethod
    async def log_admin_action(
        user_id: str,
        action: str,
        target_type: str,
        target_id: str,
        request: Request,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Log admin action"""
        await AuditLogger.log_operation(
            operation="admin_action",
            user_id=user_id,
            request=request,
            details={
                "action": action,
                "target_type": target_type,
                "target_id": target_id,
                **(details or {}),
            },
            status="success",
        )


# Global audit logger instance
audit_logger = AuditLogger()
