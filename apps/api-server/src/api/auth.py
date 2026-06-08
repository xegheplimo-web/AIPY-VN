"""
Authentication API using ECC-signed JWT tokens

Provides:
- User registration with password hashing
- Login with JWT token generation (ECDSA-signed)
- Token refresh
- Password reset
- OAuth integration endpoints
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import select
from src.database import async_session
from src.middleware.auth_middleware import require_auth
from src.models.user import User
from src.services.ecc import get_ecc_service, get_jwt_service

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRegisterRequest(BaseModel):
    """Request model for user registration"""

    email: EmailStr
    phone: str | None = Field(None, pattern=r"^(\+84|0)[0-9]{9,10}$")
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str | None = Field(None, max_length=100)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        """Validate password strength"""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLoginRequest(BaseModel):
    """Request model for user login"""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Response model for token"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh"""

    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Request model for password reset"""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Request model for password reset confirmation"""

    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


class UserResponse(BaseModel):
    """Response model for user info"""

    id: str
    email: str
    phone: str | None
    full_name: str | None
    role: str
    is_verified: bool
    created_at: str
    model_config = {"from_attributes": True}
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(data: UserRegisterRequest):
    """
    Register a new user account.

    - Validates email uniqueness
    - Hashes password using bcrypt
    - Creates user with default 'customer' role
    - Returns user info (without password)
    """
    async with async_session() as session:
        # Check if email already exists
        existing_stmt = select(User).where(User.email == data.email)
        existing_result = await session.execute(existing_stmt)
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Check if phone already exists (if provided)
        if data.phone:
            phone_stmt = select(User).where(User.phone == data.phone)
            phone_result = await session.execute(phone_stmt)
            if phone_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Phone number already registered",
                )

        # Create new user
        user = User(
            id=uuid.uuid4(),
            email=data.email,
            phone=data.phone,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            role="customer",  # Default role
            is_verified=False,
            is_active=True,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )

        session.add(user)
        await session.commit()
        await session.refresh(user)

        return UserResponse(
            id=str(user.id),
            email=user.email,
            phone=user.phone,
            full_name=user.full_name,
            role=user.role,
            is_verified=user.is_verified,
            created_at=user.created_at or datetime.now().isoformat(),
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(data: UserLoginRequest):
    """
    Authenticate user and return JWT tokens.

    - Verifies email and password
    - Generates access token (1 hour expiry)
    - Generates refresh token (7 days expiry)
    - Tokens are signed using ECDSA
    """
    async with async_session() as session:
        # Find user by email
        stmt = select(User).where(User.email == data.email)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated"
            )

        # Update last login
        user.last_login_at = datetime.now().isoformat()
        await session.commit()

        # Generate JWT tokens using ECDSA
        jwt_service = get_jwt_service()

        # Access token (1 hour)
        access_payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "type": "access",
        }
        access_token = jwt_service.create_token(access_payload, expires_in=3600)

        # Refresh token (7 days)
        refresh_payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "type": "refresh",
        }
        refresh_token = jwt_service.create_token(refresh_payload, expires_in=604800)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=3600,
            user={
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "is_verified": user.is_verified,
            },
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshTokenRequest):
    """
    Refresh access token using refresh token.

    - Validates refresh token
    - Generates new access token
    - Returns new token pair
    """
    jwt_service = get_jwt_service()

    # Verify refresh token
    payload = jwt_service.verify_token(data.refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Get user from database
    async with async_session() as session:
        stmt = select(User).where(User.id == uuid.UUID(payload["sub"]))
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        # Generate new tokens
        access_payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "type": "access",
        }
        access_token = jwt_service.create_token(access_payload, expires_in=3600)

        refresh_payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "type": "refresh",
        }
        refresh_token = jwt_service.create_token(refresh_payload, expires_in=604800)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=3600,
            user={
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "is_verified": user.is_verified,
            },
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(require_auth)):
    """
    Get current authenticated user information.

    - Requires valid JWT token
    - Returns user profile
    """
    async with async_session() as session:
        stmt = select(User).where(User.id == uuid.UUID(current_user["id"]))
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return UserResponse(
            id=str(user.id),
            email=user.email,
            phone=user.phone,
            full_name=user.full_name,
            role=user.role,
            is_verified=user.is_verified,
            created_at=user.created_at or datetime.now().isoformat(),
        )


@router.post("/logout")
async def logout_user(current_user: dict = Depends(require_auth)):
    """
    Logout user (token invalidation).

    - In production, add token to blacklist/Redis
    - Client should discard tokens
    """
    # In production: Add token to Redis blacklist
    # await redis.setex(f"blacklist:{token}", expiry, "1")

    return {"message": "Logged out successfully"}


@router.post("/password-reset/request")
async def request_password_reset(data: PasswordResetRequest):
    """
    Request password reset.

    - Generates reset token
    - Sends email with reset link (in production)
    """
    async with async_session() as session:
        stmt = select(User).where(User.email == data.email)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            # Don't reveal if email exists (security best practice)
            return {"message": "If email exists, reset link will be sent"}

        # Generate reset token (in production, use separate service)
        jwt_service = get_jwt_service()
        reset_payload = {
            "sub": str(user.id),
            "email": user.email,
            "type": "password_reset",
        }
        reset_token = jwt_service.create_token(reset_payload, expires_in=3600)  # 1 hour

        # In production: Send email with reset link
        # await send_reset_email(user.email, reset_token)

        return {
            "message": "Password reset link sent to email",
            "reset_token": reset_token,  # Only for development
        }


@router.post("/password-reset/confirm")
async def confirm_password_reset(data: PasswordResetConfirm):
    """
    Confirm password reset with token.

    - Validates reset token
    - Updates password
    """
    jwt_service = get_jwt_service()

    # Verify reset token
    payload = jwt_service.verify_token(data.token)

    if not payload or payload.get("type") != "password_reset":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired reset token",
        )

    async with async_session() as session:
        stmt = select(User).where(User.id == uuid.UUID(payload["sub"]))
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Update password
        user.password_hash = hash_password(data.new_password)
        user.updated_at = datetime.now().isoformat()

        await session.commit()

        return {"message": "Password reset successfully"}


@router.get("/public-key")
async def get_public_key():
    """
    Get the server's public key for JWT verification.

    - Returns PEM-formatted public key
    - Clients can use this to verify JWT signatures
    """
    ecc_service = get_ecc_service()
    return {
        "public_key": ecc_service.get_public_key_pem(),
        "algorithm": "ES256",
        "curve": "P-256",
    }
