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

from fastapi import APIRouter, Depends, HTTPException, Request, status
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import select
from src.database import async_session
from src.middleware.auth_middleware import require_auth
from src.models.user import User
from src.services.ecc import get_ecc_service, get_jwt_service
from src.services.audit_logger import audit_logger

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
    """Response model for token generation"""

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: dict


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register_user(data: UserRegisterRequest, request: Request):
    """
    Register a new user.

    - Hashes password using bcrypt
    - Creates user with default role "customer"
    - Returns JWT tokens
    """
    async with async_session() as session:
        # Check if user already exists
        stmt = select(User).where(User.email == data.email)
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
            )

        # Create new user
        user = User(
            id=uuid.uuid4(),
            email=data.email,
            phone=data.phone,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            role="customer",
            is_active=True,
        )

        session.add(user)
        await session.commit()
        await session.refresh(user)

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

        # Log registration
        await audit_logger.log_operation(
            operation="user_register",
            user_id=str(user.id),
            request=request,
            details={"email": user.email},
            status="success",
        )

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
                "phone": user.phone,
                "is_active": user.is_active,
                "created_at": user.created_at or datetime.now().isoformat(),
            },
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(data: UserLoginRequest, request: Request):
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
            # Log failed login attempt
            await audit_logger.log_login(
                user_id=str(user.id) if user else None,
                request=request,
                success=False,
            )
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

        # Log successful login
        await audit_logger.log_login(
            user_id=str(user.id),
            request=request,
            success=True,
        )

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
                "phone": user.phone,
                "is_active": user.is_active,
                "created_at": user.created_at or datetime.now().isoformat(),
            },
        )


@router.post("/logout")
async def logout_user(
    request: Request,
    current_user: User = Depends(require_auth),
):
    """
    Logout user.

    - Logs the logout event
    - In production, would invalidate the token
    """
    # Log logout
    await audit_logger.log_logout(
        user_id=str(current_user.id),
        request=request,
    )

    return {"message": "Logged out successfully"}
