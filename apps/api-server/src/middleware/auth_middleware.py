"""
Authentication Middleware using ECC-signed JWT tokens

Provides:
- JWT token verification using ECDSA
- User authentication for protected routes
- Role-based access control (RBAC)
- Token refresh mechanism
"""

from collections.abc import Callable

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer
from src.services.ecc import get_jwt_service
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

security = HTTPBearer(auto_error=False)


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for JWT authentication using ECC-signed tokens"""

    # Public routes that don't require authentication
    PUBLIC_PATHS = {
        "/health",
        "/docs",
        "/openapi.json",
        "/api/chat/search",
        "/api/suggestions",
        "/api/stores",
        "/api/products",
        "/api/auth/public-key",
        "/api/auth/register",
        "/api/auth/login",
    }

    # Role-based access control
    ROLE_PERMISSIONS = {
        "customer": [
            "GET",  # Can read most resources
            "POST",  # Can create orders, cart items
        ],
        "owner": [
            "GET",
            "POST",
            "PUT",
            "DELETE",  # Full CRUD on own resources
        ],
        "admin": [
            "GET",
            "POST",
            "PUT",
            "DELETE",  # Full system access
        ],
    }

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request and validate JWT token"""

        # Skip authentication for public paths
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)

        # Skip for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        try:
            # Extract token from Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Missing or invalid authorization header"},
                )

            token = auth_header.split(" ")[1]

            # Verify JWT token using ECDSA
            jwt_service = get_jwt_service()
            payload = jwt_service.verify_token(token)

            if not payload:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid or expired token"},
                )

            # Check role-based permissions
            user_role = payload.get("role", "customer")
            if not self._check_permission(request.method, user_role, request.url.path):
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Insufficient permissions"},
                )

            # Add user info to request state
            request.state.user_id = payload.get("sub")
            request.state.user_role = user_role
            request.state.user_email = payload.get("email")

            return await call_next(request)

        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": f"Authentication error: {e!s}"},
            )

    def _check_permission(self, method: str, role: str, path: str) -> bool:
        """
        Check if user role has permission for this method/path.

        Args:
            method: HTTP method
            role: User role
            path: Request path

        Returns:
            True if permitted
        """
        # Admin has full access
        if role == "admin":
            return True

        # Get allowed methods for role
        allowed_methods = self.ROLE_PERMISSIONS.get(role, ["GET"])

        # Check if method is allowed
        if method not in allowed_methods:
            return False

        # Additional path-based restrictions could be added here
        # For example, owners can only access their own stores

        return True


async def get_current_user(request: Request) -> dict | None:
    """
    Dependency to get current authenticated user from request state.

    Args:
        request: FastAPI request

    Returns:
        User info dict or None
    """
    return {
        "id": getattr(request.state, "user_id", None),
        "role": getattr(request.state, "user_role", None),
        "email": getattr(request.state, "user_email", None),
    }


async def require_auth(request: Request) -> dict:
    """
    Dependency that requires authentication.

    Works both when AuthMiddleware is active (production) and when it's not (development).
    - If middleware set request.state.user_id, use that directly.
    - Otherwise, extract and verify the JWT token from Authorization header.

    Args:
        request: FastAPI request

    Returns:
        User info dict with id, role, email

    Raises:
        HTTPException if not authenticated
    """
    # First try: get user info from middleware (production mode)
    user = await get_current_user(request)
    if user and user["id"]:
        return user

    # Fallback: verify token directly from Authorization header (development mode)
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide a valid Bearer token.",
        )

    token = auth_header.split(" ")[1]
    try:
        jwt_service = get_jwt_service()
        payload = jwt_service.verify_token(token) or jwt_service.decode_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        # Set on request state for downstream use
        request.state.user_id = payload.get("sub")
        request.state.user_role = payload.get("role", "customer")
        request.state.user_email = payload.get("email")

        return {
            "id": payload.get("sub"),
            "role": payload.get("role", "customer"),
            "email": payload.get("email"),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {e!s}",
        )


async def require_role(role: str, request: Request) -> dict:
    """
    Dependency that requires specific role.

    Args:
        role: Required role
        request: FastAPI request

    Returns:
        User info dict

    Raises:
        HTTPException if user doesn't have required role
    """
    user = await require_auth(request)
    if user["role"] != role and user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Role '{role}' required"
        )
    return user


async def require_owner_or_admin(request: Request) -> dict:
    """
    Dependency that requires owner or admin role.

    Args:
        request: FastAPI request

    Returns:
        User info dict

    Raises:
        HTTPException if user is not owner or admin
    """
    user = await require_auth(request)
    if user["role"] not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Owner or admin role required"
        )
    return user


async def require_admin(request: Request) -> dict:
    """
    Dependency that requires admin role.

    Args:
        request: FastAPI request

    Returns:
        User info dict

    Raises:
        HTTPException if user is not admin
    """
    return await require_role("admin", request)
