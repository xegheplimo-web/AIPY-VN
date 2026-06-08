from sqlalchemy import Column, String, Text, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.database import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id"))
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")
    is_read = Column(Boolean, default=False)
    created_at = Column(String, default="now()")
