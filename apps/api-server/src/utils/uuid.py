"""
UUID utility for safe UUID conversion and validation.

Provides consistent UUID handling across the application.
"""

import uuid

from fastapi import HTTPException, status


def safe_uuid(uuid_str: str) -> uuid.UUID:
    """
    Safely convert string to UUID with error handling.

    Args:
        uuid_str: UUID string to convert

    Returns:
        UUID object

    Raises:
        HTTPException: If the string is not a valid UUID

    Example:
        >>> user_id = safe_uuid("123e4567-e89b-12d3-a456-426614174000")
        >>> stmt = select(User).where(User.id == user_id)
    """
    try:
        return uuid.UUID(uuid_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {uuid_str}",
        )


def validate_uuid(uuid_str: str) -> bool:
    """
    Validate if a string is a valid UUID without raising exception.

    Args:
        uuid_str: String to validate

    Returns:
        True if valid UUID, False otherwise

    Example:
        >>> if validate_uuid(user_id):
        ...     # Proceed with UUID operations
    """
    if uuid_str is None:
        return False
    try:
        uuid.UUID(uuid_str)
        return True
    except (ValueError, TypeError, AttributeError):
        return False
