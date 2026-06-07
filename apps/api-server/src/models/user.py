from sqlalchemy import Column, String, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20), unique=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    avatar_url = Column(String(500))
    role = Column(String(20), default="customer")
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    last_login_at = Column(String)
    created_at = Column(String, default="now()")
    updated_at = Column(String, default="now()")


class Address(Base):
    __tablename__ = "addresses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    label = Column(String(50))
    full_address = Column(Text, nullable=False)
    ward = Column(String(100))
    district = Column(String(100))
    province = Column(String(100))
    postal_code = Column(String(20))
    latitude = Column(String)
    longitude = Column(String)
    is_default = Column(Boolean, default=False)
    created_at = Column(String, default="now()")
