"""
User Profile API

Endpoints for managing user profile information.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy import select, and_

from src.db import async_session
from src.models.user import User, Address
from src.middleware.auth_middleware import get_current_user, require_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users/me", tags=["User Profile"])


class ProfileUpdateRequest(BaseModel):
    """Request to update user profile."""

    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r"^(\+84|0)[0-9]{9,10}$")
    avatar_url: Optional[str] = None


class ProfileResponse(BaseModel):
    """Response model for user profile."""

    id: str
    email: str
    phone: Optional[str]
    full_name: Optional[str]
    avatar_url: Optional[str]
    role: str
    is_verified: bool
    is_active: bool
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True


class AddressRequest(BaseModel):
    """Request to create or update an address."""

    full_name: str = Field(..., max_length=100)
    phone: str = Field(..., pattern=r"^(\+84|0)[0-9]{9,10}$")
    address_line: str = Field(..., max_length=255)
    city: str = Field(..., max_length=100)
    district: str = Field(..., max_length=100)
    ward: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    is_default: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class AddressResponse(BaseModel):
    """Response model for address."""

    id: str
    user_id: str
    full_name: str
    phone: str
    address_line: str
    city: str
    district: str
    ward: Optional[str]
    postal_code: Optional[str]
    is_default: bool
    latitude: Optional[float]
    longitude: Optional[float]
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(current_user: User = Depends(require_auth)):
    """Get current user's profile information."""
    return ProfileResponse(
        id=str(current_user.id),
        email=current_user.email,
        phone=current_user.phone,
        full_name=current_user.full_name,
        avatar_url=current_user.avatar_url,
        role=current_user.role,
        is_verified=current_user.is_verified,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )


@router.put("/profile", response_model=ProfileResponse)
async def update_profile(
    data: ProfileUpdateRequest,
    current_user: User = Depends(require_auth),
):
    """
    Update current user's profile information.

    - Email uniqueness will be checked if email is being changed
    """
    async with async_session() as session:
        # Check email uniqueness if email is being changed
        if data.email and data.email != current_user.email:
            existing_query = select(User).where(User.email == data.email)
            existing_result = await session.execute(existing_query)
            if existing_result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Email already in use")

        # Update user profile
        if data.full_name is not None:
            current_user.full_name = data.full_name
        if data.email is not None:
            current_user.email = data.email
        if data.phone is not None:
            current_user.phone = data.phone
        if data.avatar_url is not None:
            current_user.avatar_url = data.avatar_url

        await session.commit()
        await session.refresh(current_user)

        return ProfileResponse(
            id=str(current_user.id),
            email=current_user.email,
            phone=current_user.phone,
            full_name=current_user.full_name,
            avatar_url=current_user.avatar_url,
            role=current_user.role,
            is_verified=current_user.is_verified,
            is_active=current_user.is_active,
            created_at=current_user.created_at,
            updated_at=current_user.updated_at,
        )


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(require_auth),
):
    """
    Upload user avatar image.

    TODO: Implement actual file upload to cloud storage (S3, Cloudinary, etc.)
    For now, returns a mock URL.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # TODO: Upload to cloud storage and get URL
    # For now, return a placeholder URL
    avatar_url = f"https://example.com/avatars/{current_user.id}/{file.filename}"

    async with async_session() as session:
        current_user.avatar_url = avatar_url
        await session.commit()
        await session.refresh(current_user)

    return {"avatar_url": avatar_url, "message": "Avatar uploaded successfully"}


@router.get("/addresses", response_model=List[AddressResponse])
async def get_addresses(current_user: User = Depends(require_auth)):
    """Get all addresses for the current user."""
    async with async_session() as session:
        query = (
            select(Address)
            .where(Address.user_id == current_user.id)
            .order_by(Address.is_default.desc(), Address.created_at.desc())
        )
        result = await session.execute(query)
        addresses = result.scalars().all()

        return [
            AddressResponse(
                id=str(addr.id),
                user_id=str(addr.user_id),
                full_name=addr.full_name,
                phone=addr.phone,
                address_line=addr.address_line,
                city=addr.city,
                district=addr.district,
                ward=addr.ward,
                postal_code=addr.postal_code,
                is_default=addr.is_default,
                latitude=addr.latitude,
                longitude=addr.longitude,
                created_at=addr.created_at,
                updated_at=addr.updated_at,
            )
            for addr in addresses
        ]


@router.post("/addresses", response_model=AddressResponse, status_code=201)
async def create_address(
    data: AddressRequest,
    current_user: User = Depends(require_auth),
):
    """
    Create a new address for the current user.

    - If is_default is True, will set other addresses to non-default
    """
    async with async_session() as session:
        # If setting as default, unset other default addresses
        if data.is_default:
            update_query = select(Address).where(
                and_(Address.user_id == current_user.id, Address.is_default == True)
            )
            result = await session.execute(update_query)
            default_addresses = result.scalars().all()
            for addr in default_addresses:
                addr.is_default = False

        # Create new address
        address = Address(
            user_id=current_user.id,
            full_name=data.full_name,
            phone=data.phone,
            address_line=data.address_line,
            city=data.city,
            district=data.district,
            ward=data.ward,
            postal_code=data.postal_code,
            is_default=data.is_default,
            latitude=data.latitude,
            longitude=data.longitude,
        )

        session.add(address)
        await session.commit()
        await session.refresh(address)

        return AddressResponse(
            id=str(address.id),
            user_id=str(address.user_id),
            full_name=address.full_name,
            phone=address.phone,
            address_line=address.address_line,
            city=address.city,
            district=address.district,
            ward=address.ward,
            postal_code=address.postal_code,
            is_default=address.is_default,
            latitude=address.latitude,
            longitude=address.longitude,
            created_at=address.created_at,
            updated_at=address.updated_at,
        )


@router.put("/addresses/{address_id}", response_model=AddressResponse)
async def update_address(
    address_id: str,
    data: AddressRequest,
    current_user: User = Depends(require_auth),
):
    """
    Update an existing address.

    - User can only update their own addresses
    - If setting as default, will unset other default addresses
    """
    async with async_session() as session:
        query = select(Address).where(Address.id == address_id)
        result = await session.execute(query)
        address = result.scalar_one_or_none()

        if not address:
            raise HTTPException(status_code=404, detail="Address not found")

        if address.user_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="You can only update your own addresses"
            )

        # If setting as default, unset other default addresses
        if data.is_default and not address.is_default:
            update_query = select(Address).where(
                and_(
                    Address.user_id == current_user.id,
                    Address.id != address_id,
                    Address.is_default == True,
                )
            )
            result = await session.execute(update_query)
            default_addresses = result.scalars().all()
            for addr in default_addresses:
                addr.is_default = False

        # Update address
        address.full_name = data.full_name
        address.phone = data.phone
        address.address_line = data.address_line
        address.city = data.city
        address.district = data.district
        address.ward = data.ward
        address.postal_code = data.postal_code
        address.is_default = data.is_default
        address.latitude = data.latitude
        address.longitude = data.longitude

        await session.commit()
        await session.refresh(address)

        return AddressResponse(
            id=str(address.id),
            user_id=str(address.user_id),
            full_name=address.full_name,
            phone=address.phone,
            address_line=address.address_line,
            city=address.city,
            district=address.district,
            ward=address.ward,
            postal_code=address.postal_code,
            is_default=address.is_default,
            latitude=address.latitude,
            longitude=address.longitude,
            created_at=address.created_at,
            updated_at=address.updated_at,
        )


@router.delete("/addresses/{address_id}")
async def delete_address(
    address_id: str,
    current_user: User = Depends(require_auth),
):
    """
    Delete an address.

    - User can only delete their own addresses
    - Cannot delete default address if it's the only address
    """
    async with async_session() as session:
        query = select(Address).where(Address.id == address_id)
        result = await session.execute(query)
        address = result.scalar_one_or_none()

        if not address:
            raise HTTPException(status_code=404, detail="Address not found")

        if address.user_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="You can only delete your own addresses"
            )

        # Check if it's the only address
        count_query = select(Address).where(Address.user_id == current_user.id)
        count_result = await session.execute(count_query)
        total_addresses = count_result.scalar() or 0

        if total_addresses == 1:
            raise HTTPException(
                status_code=400, detail="Cannot delete your only address"
            )

        # If deleting default address, set another as default
        if address.is_default:
            other_query = (
                select(Address)
                .where(
                    and_(
                        Address.user_id == current_user.id,
                        Address.id != address_id,
                    )
                )
                .order_by(Address.created_at)
            )
            other_result = await session.execute(other_query)
            other_address = other_result.scalar_one_or_none()
            if other_address:
                other_address.is_default = True

        await session.delete(address)
        await session.commit()

        return {"message": "Address deleted successfully"}


@router.post("/addresses/{address_id}/set-default", response_model=AddressResponse)
async def set_default_address(
    address_id: str,
    current_user: User = Depends(require_auth),
):
    """
    Set an address as the default address.

    - User can only set their own addresses as default
    - Will unset other default addresses
    """
    async with async_session() as session:
        query = select(Address).where(Address.id == address_id)
        result = await session.execute(query)
        address = result.scalar_one_or_none()

        if not address:
            raise HTTPException(status_code=404, detail="Address not found")

        if address.user_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="You can only set your own addresses"
            )

        # Unset other default addresses
        update_query = select(Address).where(
            and_(
                Address.user_id == current_user.id,
                Address.id != address_id,
                Address.is_default == True,
            )
        )
        result = await session.execute(update_query)
        default_addresses = result.scalars().all()
        for addr in default_addresses:
            addr.is_default = False

        # Set this address as default
        address.is_default = True

        await session.commit()
        await session.refresh(address)

        return AddressResponse(
            id=str(address.id),
            user_id=str(address.user_id),
            full_name=address.full_name,
            phone=address.phone,
            address_line=address.address_line,
            city=address.city,
            district=address.district,
            ward=address.ward,
            postal_code=address.postal_code,
            is_default=address.is_default,
            latitude=address.latitude,
            longitude=address.longitude,
            created_at=address.created_at,
            updated_at=address.updated_at,
        )
