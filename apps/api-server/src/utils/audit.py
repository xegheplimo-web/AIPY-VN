"""
Audit Logging Utility

Provides structured logging for security-relevant events.
"""

import json
import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import Request

logger = logging.getLogger(__name__)


class AuditLogger:
    """Structured audit logger for security events."""

    @staticmethod
    def log_event(
        event_type: str,
        user_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        resource: str | None = None,
        action: str | None = None,
        details: dict[str, Any] | None = None,
        success: bool = True,
    ):
        """
        Log an audit event.

        Args:
            event_type: Type of event (e.g., "login", "data_access", "permission_denied")
            user_id: User ID if available
            ip_address: Client IP address
            user_agent: Client user agent
            resource: Resource being accessed
            action: Action being performed
            details: Additional event details
            success: Whether the operation succeeded
        """
        audit_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "resource": resource,
            "action": action,
            "success": success,
            "details": details or {},
        }

        # Log with appropriate level
        if success:
            logger.info(f"AUDIT: {json.dumps(audit_data)}")
        else:
            logger.warning(f"AUDIT: {json.dumps(audit_data)}")

    @staticmethod
    def log_login(user_id: str, ip_address: str, user_agent: str, success: bool = True):
        """Log login attempt."""
        AuditLogger.log_event(
            event_type="login",
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
        )

    @staticmethod
    def log_logout(user_id: str, ip_address: str):
        """Log logout event."""
        AuditLogger.log_event(
            event_type="logout",
            user_id=user_id,
            ip_address=ip_address,
        )

    @staticmethod
    def log_permission_denied(
        user_id: str,
        resource: str,
        action: str,
        ip_address: str,
        details: dict[str, Any] | None = None,
    ):
        """Log permission denied event."""
        AuditLogger.log_event(
            event_type="permission_denied",
            user_id=user_id,
            resource=resource,
            action=action,
            ip_address=ip_address,
            details=details,
            success=False,
        )

    @staticmethod
    def log_data_access(
        user_id: str,
        resource: str,
        action: str,
        ip_address: str,
        details: dict[str, Any] | None = None,
    ):
        """Log data access event."""
        AuditLogger.log_event(
            event_type="data_access",
            user_id=user_id,
            resource=resource,
            action=action,
            ip_address=ip_address,
            details=details,
        )

    @staticmethod
    def log_data_modification(
        user_id: str,
        resource: str,
        action: str,
        ip_address: str,
        details: dict[str, Any] | None = None,
    ):
        """Log data modification event."""
        AuditLogger.log_event(
            event_type="data_modification",
            user_id=user_id,
            resource=resource,
            action=action,
            ip_address=ip_address,
            details=details,
        )

    @staticmethod
    def log_from_request(request: Request, event_type: str, **kwargs):
        """Log audit event from FastAPI request."""
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        AuditLogger.log_event(
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
            **kwargs,
        )


# Global audit logger instance
audit_logger = AuditLogger()
