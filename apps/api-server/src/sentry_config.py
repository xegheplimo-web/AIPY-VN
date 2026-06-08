"""
Sentry Error Tracking Configuration

Initializes Sentry for error tracking and performance monitoring.
"""

import logging

from sentry_sdk import init as sentry_init
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from src.config import config

logger = logging.getLogger(__name__)


def init_sentry():
    """Initialize Sentry for error tracking."""
    if not config.sentry.is_configured():
        logger.info("Sentry not configured, skipping initialization")
        return

    try:
        sentry_init(
            dsn=config.sentry.dsn,
            environment=config.sentry.environment,
            sample_rate=config.sentry.sample_rate,
            traces_sample_rate=config.sentry.traces_sample_rate,
            profiles_sample_rate=config.sentry.profiles_sample_rate,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
                CeleryIntegration(),
            ],
            # Before send callback to filter sensitive data
            before_send=before_send,
            # Before breadcrumb callback to filter sensitive breadcrumbs
            before_breadcrumb=before_breadcrumb,
            # Release version (optional)
            # release="v1.0.0",
        )
        logger.info(f"Sentry initialized for environment: {config.sentry.environment}")
        
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def before_send(event, hint):
    """
    Filter sensitive data before sending to Sentry.
    
    Args:
        event: Sentry event
        hint: Sentry hint
    
    Returns:
        Modified event or None to drop the event
    """
    # Filter out sensitive data
    if event.get("request"):
        # Remove sensitive headers
        request = event["request"]
        if "headers" in request:
            sensitive_headers = ["authorization", "cookie", "x-api-key"]
            request["headers"] = {
                k: v for k, v in request["headers"].items()
                if k.lower() not in sensitive_headers
            }
    
    # Filter out certain exceptions
    if "exc_info" in hint:
        exc_type, exc_value, exc_tb = hint["exc_info"]
        # Don't send certain exceptions to Sentry
        if exc_type.__name__ in ["KeyboardInterrupt", "SystemExit"]:
            return None
    
    return event


def before_breadcrumb(breadcrumb, hint):
    """
    Filter sensitive breadcrumbs.
    
    Args:
        breadcrumb: Sentry breadcrumb
        hint: Sentry hint
    
    Returns:
        Modified breadcrumb or None to drop the breadcrumb
    """
    # Filter out sensitive breadcrumbs
    if breadcrumb.get("category") == "http":
        if "data" in breadcrumb:
            # Remove sensitive data from HTTP requests
            sensitive_keys = ["password", "token", "api_key", "secret"]
            breadcrumb["data"] = {
                k: v for k, v in breadcrumb["data"].items()
                if k.lower() not in sensitive_keys
            }
    
    return breadcrumb
