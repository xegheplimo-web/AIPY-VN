"""
User Profile API

Endpoints for managing user profile information.
"""

import logging
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import and_, select
from src.database import async_session
from src.middleware.auth_middleware import require_auth
from src.models.user import Address, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users/me", tags=["User Profile"])

# Allowed image extensions and MIME types
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Upload directory (relative to project root)
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "avatars")


class ProfileUpdateRequest(BaseModel):
    """Request to update user profile."""

    full_name: str | None = Field(None, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(None, pattern=r"^(\+84|0)[0-9]{9,10}$")
    avatar_url: str | None = None


class ProfileResponse(BaseModel):
    """Response model for user profile."""

    id: str
    email: str
    phone: str | None
    full_name: str | None
    avatar_url: str | None
    role: str
    is_verified: bool
    is_active: bool
    created_at: str
    updated_at: str | None
    model_config = {"from_attributes": True}


class AddressRequest(BaseModel):
    """Request to create or update an address."""

    full_name: str = Field(..., max_length=100)
    phone: str = Field(..., pattern=r"^(\+84|0)[0-9]{9,10}$")
    address_line: str = Field(..., max_length=255)
    city: str = Field(..., max_length=100)
    district: str = Field(..., max_length=100)
    ward: str | None = Field(None, max_length=100)
    postal_code: str | None = Field(None, max_length=20)
    is_default: bool = False
    latitude: float | None = None
    longitude: float | None = None


class AddressResponse(BaseModel):
    """Response model for address."""

    id: str
    user_id: str
    full_name: str
    phone: str
    address_line: str
    city: str
    district: str
    ward: str | None
    postal_code: str | None
    is_default: bool
    latitude: float | None
    longitude: float | None
    created_at: str
    updated_at: str | None
    model_config = {"from_attributes": True}


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(current_user: User = Depends(require_auth)):
    """Get current user's profile information."""
    user_id = current_user["id"] if isinstance(current_user, dict) else current_user.id
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return ProfileResponse(
            id=str(user.id),
            email=user.email,
            phone=user.phone,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            role=user.role,
            is_verified=user.is_verified,
            is_active=user.is_active,
            created_at=str(user.created_at) if user.created_at else "",
            updated_at=str(user.updated_at) if user.updated_at else None,
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
    user_id = current_user["id"] if isinstance(current_user, dict) else current_user.id
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check email uniqueness if email is being changed
        if data.email and data.email != user.email:
            existing_query = select(User).where(User.email == data.email)
            existing_result = await session.execute(existing_query)
            if existing_result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Email already in use")

        # Update user profile
        if data.full_name is not None:
            user.full_name = data.full_name
        if data.email is not None:
            user.email = data.email
        if data.phone is not None:
            user.phone = data.phone
        if data.avatar_url is not None:
            user.avatar_url = data.avatar_url

        await session.commit()
        await session.refresh(user)

        return ProfileResponse(
            id=str(user.id),
            email=user.email,
            phone=user.phone,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            role=user.role,
            is_verified=user.is_verified,
            is_active=user.is_active,
            created_at=str(user.created_at) if user.created_at else "",
            updated_at=str(user.updated_at) if user.updated_at else None,
        )


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(require_auth),
):
    """
    Upload user avatar image.

    - Accepts jpg, jpeg, png, webp formats only
    - Maximum file size: 5MB
    - Saves to local uploads/avatars/ directory
    - Returns the relative URL path for the uploaded avatar
    """
    user_id = current_user["id"] if isinstance(current_user, dict) else current_user.id

    # Validate file content type
    if not file.content_type or file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Validate file extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    file_ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Read file content and validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds the maximum limit of {MAX_FILE_SIZE // (1024 * 1024)}MB",
        )

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # Ensure upload directory exists
    upload_dir = os.path.abspath(UPLOAD_DIR)
    try:
        os.makedirs(upload_dir, exist_ok=True)
    except OSError as e:
        logger.error(f"Failed to create upload directory {upload_dir}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Avatar upload service is currently unavailable. Please try again later.",
        )

    # Check if directory is writable
    if not os.access(upload_dir, os.W_OK):
        logger.error(f"Upload directory is not writable: {upload_dir}")
        raise HTTPException(
            status_code=500,
            detail="Avatar upload service is currently unavailable. Please try again later.",
        )

    # Generate unique filename
    unique_id = uuid.uuid4().hex[:8]
    filename = f"{user_id}_{unique_id}.{file_ext}"
    file_path = os.path.join(upload_dir, filename)

    # Save file to disk
    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except OSError as e:
        logger.error(f"Failed to save avatar file to {file_path}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to save avatar. Please try again later.",
        )

    # Build the relative URL path
    avatar_url = f"/uploads/avatars/{filename}"

    # Update user avatar_url in database
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            # Clean up the uploaded file if user not found
            try:
                os.remove(file_path)
            except OSError:
                pass
            raise HTTPException(status_code=404, detail="User not found")

        # Remove old avatar file if it was a local upload
        if user.avatar_url and user.avatar_url.startswith("/uploads/avatars/"):
            old_filename = user.avatar_url.split("/")[-1]
            old_file_path = os.path.join(upload_dir, old_filename)
            try:
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
            except OSError as e:
                logger.warning(f"Failed to remove old avatar {old_file_path}: {e}")

        user.avatar_url = avatar_url
        await session.commit()

    logger.info(f"Avatar uploaded successfully for user {user_id}: {avatar_url}")

    return {"avatar_url": avatar_url, "message": "Avatar uploaded successfully"}


@router.get("/addresses", response_model=list[AddressResponse])
async def get_addresses(current_user: User = Depends(require_auth)):
    """Get all addresses for the current user."""
    user_id = current_user["id"] if isinstance(current_user, dict) else current_user.id
    async with async_session() as session:
        query = (
            select(Address)
            .where(Address.user_id == user_id)
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
                created_at=str(addr.created_at) if addr.created_at else "",
                updated_at=str(addr.updated_at) if addr.updated_at else None,
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
    user_id = current_user["id"] if isinstance(current_user, dict) else current_user.id
    async with async_session() as session:
        # If setting as default, unset other default addresses
        if data.is_default:
            update_query = select(Address).where(
                and_(Address.user_id == user_id, Address.is_default)
            )
            result = await session.execute(update_query)
            default_addresses = result.scalars().all()
            for addr in default_addresses:
                addr.is_default = False

        # Create new address
        address = Address(
            user_id=user_id,
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
            created_at=str(address.created_at) if address.created_at else "",
            updated_at=str(address.updated_at) if address.updated_at else None,
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
    user_id = current_user["id"] if isinstance(current_user, dict) else current_user.id
    async with async_session() as session:
        query = select(Address).where(Address.id == address_id)
        result = await session.execute(query)
        address = result.scalar_one_or_none()

        if not address:
            raise HTTPException(status_code=404, detail="Address not found")

        if address.user_id != user_id:
            raise HTTPException(
                status_code=403, detail="You can only update your own addresses"
            )

        # If setting as default, unset other default addresses
        if data.is_default and not address.is_default:
            update_query = select(Address).where(
                and_(
                    Address.user_id == user_id,
                    Address.id != address_id,
                    Address.is_default,
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
            created_at=str(address.created_at) if address.created_at else "",
            updated_at=str(address.updated_at) if address.updated_at else None,
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
    user_id = current_user["id"] if isinstance(current_user, dict) else current_user.id
    async with async_session() as session:
        query = select(Address).where(Address.id == address_id)
        result = await session.execute(query)
        address = result.scalar_one_or_none()

        if not address:
            raise HTTPException(status_code=404, detail="Address not found")

        if address.user_id != user_id:
            raise HTTPException(
                status_code=403, detail="You can only delete your own addresses"
            )

        # Check if it's the only address
        count_query = select(Address).where(Address.user_id == user_id)
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
                        Address.user_id == user_id,
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
    user_id = current_user["id"] if isinstance(current_user, dict) else current_user.id
    async with async_session() as session:
        query = select(Address).where(Address.id == address_id)
        result = await session.execute(query)
        address = result.scalar_one_or_none()

        if not address:
            raise HTTPException(status_code=404, detail="Address not found")

        if address.user_id != user_id:
            raise HTTPException(
                status_code=403, detail="You can only set your own addresses"
            )

        # Unset other default addresses
        update_query = select(Address).where(
            and_(
                Address.user_id == user_id,
                Address.id != address_id,
                Address.is_default,
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
            created_at=str(address.created_at) if address.created_at else "",
            updated_at=str(address.updated_at) if address.updated_at else None,
        )
