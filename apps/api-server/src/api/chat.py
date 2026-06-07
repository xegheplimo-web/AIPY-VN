import uuid
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, WebSocket, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from src.db import async_session
from src.models.chat import Message
from src.models.store import Store
from src.models.user import User

router = APIRouter(prefix="/api", tags=["Chat"])


class MessageItem(BaseModel):
    id: str
    sender_id: Optional[str] = None
    store_id: Optional[str] = None
    content: str
    message_type: str
    is_read: bool
    created_at: str

    class Config:
        from_attributes = True


class MessagesResponse(BaseModel):
    messages: List[MessageItem]
    total: int
    store_id: str


class SendMessageRequest(BaseModel):
    sender_id: str
    store_id: str
    content: str = Field(..., min_length=1)
    message_type: str = Field(default="text")


class SendMessageResponse(BaseModel):
    id: str
    status: str
    message: str


@router.get("/stores/{store_id}/messages", response_model=MessagesResponse)
async def get_store_messages(
    store_id: str,
    page: int = 1,
    limit: int = 50,
):
    async with async_session() as session:
        # Verify store exists
        store_stmt = select(Store).where(Store.id == uuid.UUID(store_id))
        store_result = await session.execute(store_stmt)
        store = store_result.scalar_one_or_none()
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")

        # Count total
        count_stmt = select(func.count(Message.id)).where(
            Message.store_id == uuid.UUID(store_id)
        )
        count_result = await session.execute(count_stmt)
        total = count_result.scalar_one()

        # Get messages paginated
        offset = (page - 1) * limit
        stmt = (
            select(Message)
            .where(Message.store_id == uuid.UUID(store_id))
            .order_by(Message.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(stmt)
        messages = result.scalars().all()

        items = [
            MessageItem(
                id=str(m.id),
                sender_id=str(m.sender_id) if m.sender_id else None,
                store_id=str(m.store_id) if m.store_id else None,
                content=m.content,
                message_type=m.message_type,
                is_read=m.is_read,
                created_at=m.created_at or datetime.now().isoformat(),
            )
            for m in messages
        ]

        return MessagesResponse(
            messages=items,
            total=total,
            store_id=store_id,
        )


@router.post("/messages", response_model=SendMessageResponse)
async def send_message(data: SendMessageRequest):
    async with async_session() as session:
        message = Message(
            id=uuid.uuid4(),
            conversation_id=uuid.uuid4(),
            sender_id=uuid.UUID(data.sender_id),
            store_id=uuid.UUID(data.store_id),
            content=data.content,
            message_type=data.message_type,
            is_read=False,
            created_at=datetime.now().isoformat(),
        )
        session.add(message)
        await session.commit()

        return SendMessageResponse(
            id=str(message.id),
            status="sent",
            message="Message sent successfully",
        )


@router.websocket("/ws/chat/{store_id}")
async def websocket_chat(websocket: WebSocket, store_id: str):
    """WebSocket endpoint for real-time chat.

    TODO: In production, implement proper WebSocket connection management
    with Redis pub/sub for multi-instance support.
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for now - full implementation would broadcast to room
            await websocket.send_text(f"Echo: {data}")
    except Exception:
        pass
