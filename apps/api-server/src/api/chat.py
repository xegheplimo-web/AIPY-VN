import uuid
import base64
import logging
from typing import List, Optional, Dict
from datetime import datetime

from fastapi import (
    APIRouter,
    WebSocket,
    HTTPException,
    Depends,
    WebSocketDisconnect,
    UploadFile,
    File,
)
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from src.database import async_session
from src.models.chat import Message
from src.models.store import Store
from src.models.user import User
from src.services.ecc import get_ecc_service, get_e2e_service
from src.services.llm import get_ollama_service
from src.services.voice import get_voice_service
from src.agents import get_shopping_agent
from src.middleware.auth_middleware import require_auth

router = APIRouter(prefix="/api", tags=["Chat"])
logger = logging.getLogger(__name__)


class MessageItem(BaseModel):
    id: str
    sender_id: Optional[str] = None
    store_id: Optional[str] = None
    content: str
    message_type: str
    is_read: bool
    created_at: str
    model_config = {"from_attributes": True}


class MessagesResponse(BaseModel):
    messages: List[MessageItem]
    total: int
    store_id: str


class SendMessageRequest(BaseModel):
    sender_id: str
    store_id: str
    content: str = Field(..., min_length=1)
    message_type: str = Field(default="text")
    encrypted: bool = Field(default=False)
    session_id: Optional[str] = None
    ciphertext: Optional[str] = None
    nonce: Optional[str] = None


class KeyExchangeRequest(BaseModel):
    """Request for ECDH key exchange"""

    store_id: str
    public_key: str  # Base64-encoded public key bytes


class KeyExchangeResponse(BaseModel):
    """Response with server's public key and session info"""

    server_public_key: str
    session_id: str


class SendMessageResponse(BaseModel):
    id: str
    status: str
    message: str


class ChatSearchRequest(BaseModel):
    """Request for AI-powered chat search"""

    query: str = Field(..., min_length=1, description="Search query")
    location: Optional[Dict[str, float]] = Field(
        None, description="User location {lat, lng}"
    )
    radius_km: Optional[int] = Field(5, description="Search radius in km")
    model: Optional[str] = Field(None, description="Ollama model to use")


class ChatSearchResponse(BaseModel):
    """Response from AI chat search"""

    summary: str
    stores: List[Dict]
    total_found: int


class VoiceSearchRequest(BaseModel):
    """Request for voice search"""

    model: str = Field(default="base", description="Whisper model size")


class VoiceSearchResponse(BaseModel):
    """Response from voice search"""

    text: str
    success: bool
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


@router.post("/messages/key-exchange", response_model=KeyExchangeResponse)
async def key_exchange(
    data: KeyExchangeRequest, current_user: dict = Depends(require_auth)
):
    """
    Establish ECDH key exchange for end-to-end encrypted chat.

    - Client sends their public key
    - Server responds with its public key
    - Both derive shared secret independently
    - Returns session_id for encryption
    """
    try:
        ecc_service = get_ecc_service()
        e2e_service = get_e2e_service()

        # Decode client's public key
        client_public_key_bytes = base64.b64decode(data.public_key)

        # Generate session key using ECDH
        session_id, aes_key = e2e_service.generate_session_key(client_public_key_bytes)

        # Get server's public key
        server_public_key_bytes = ecc_service.get_public_key_bytes()
        server_public_key_b64 = base64.b64encode(server_public_key_bytes).decode()

        return KeyExchangeResponse(
            server_public_key=server_public_key_b64, session_id=session_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Key exchange failed: {str(e)}",
        )


@router.post("/messages", response_model=SendMessageResponse)
async def send_message(
    data: SendMessageRequest, current_user: dict = Depends(require_auth)
):
    async with async_session() as session:
        # Handle encrypted messages
        content = data.content
        if data.encrypted and data.ciphertext and data.nonce and data.session_id:
            try:
                e2e_service = get_e2e_service()
                encrypted_data = {"ciphertext": data.ciphertext, "nonce": data.nonce}
                content = e2e_service.decrypt_chat_message(encrypted_data)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Decryption failed: {str(e)}",
                )

        message = Message(
            id=uuid.uuid4(),
            conversation_id=uuid.uuid4(),
            sender_id=uuid.UUID(data.sender_id),
            store_id=uuid.UUID(data.store_id),
            content=content,
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


# In-memory room management (use Redis pub/sub for production multi-instance)
room_connections: dict[str, list[WebSocket]] = {}


@router.websocket("/ws/chat/{store_id}")
async def websocket_chat(websocket: WebSocket, store_id: str):
    """WebSocket endpoint for real-time chat with room management."""
    await websocket.accept()

    # Join room
    if store_id not in room_connections:
        room_connections[store_id] = []
    room_connections[store_id].append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            # Broadcast to all connections in the room
            disconnected = []
            for conn in room_connections.get(store_id, []):
                try:
                    await conn.send_text(data)
                except Exception as e:
                    logger.warning(f"Failed to send to client in room {store_id}: {e}")
                    disconnected.append(conn)
            # Clean up disconnected clients
            for conn in disconnected:
                room_connections[store_id].remove(conn)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {store_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {store_id}: {e}")
        raise
    finally:
        # Leave room
        if store_id in room_connections and websocket in room_connections[store_id]:
            room_connections[store_id].remove(websocket)
            if not room_connections[store_id]:
                del room_connections[store_id]


@router.post("/voice/search", response_model=VoiceSearchResponse)
async def voice_search(
    audio: UploadFile = File(..., description="Audio file for transcription"),
    model: str = "base",
):
    """
    Voice search using faster-whisper speech-to-text.

    This endpoint transcribes audio to text and then uses the AI agent
    to process the search query.
    """
    try:
        voice_service = get_voice_service()

        if not voice_service.is_ready():
            return VoiceSearchResponse(
                text="",
                success=False,
                message="Dịch vụ giọng nói chưa sẵn sàng. Vui lòng thử lại sau.",
            )

        # Save uploaded file temporarily
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(await audio.read())
            temp_path = temp_file.name

        try:
            # Transcribe audio
            transcribed_text = await voice_service.transcribe_audio(
                temp_path, language="vi"
            )

            # Use AI agent to process the transcribed text
            agent = get_shopping_agent()
            response = await agent.search_products(transcribed_text)

            return VoiceSearchResponse(
                text=transcribed_text,
                success=True,
                message=f"Đã chuyển đổi giọng nói thành công. {response}",
            )

        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as e:
        logger.error(f"Voice search error: {e}")
        return VoiceSearchResponse(
            text="", success=False, message=f"Voice search failed: {str(e)}"
        )


@router.post("/chat/search", response_model=ChatSearchResponse)
async def chat_search(request: ChatSearchRequest):
    """
    AI-powered chat search using Shopping Agent.

    This endpoint uses the AI agent to generate intelligent search responses
    based on user queries and context.
    """
    try:
        agent = get_shopping_agent()

        # Build context for the agent
        context = {"location": request.location, "search_type": "product_search"}

        # Get AI response from agent
        response = await agent.search_products(
            query=request.query, location=request.location
        )

        # For now, return a mock response with the AI-generated summary
        # In production, this would integrate with actual product/store search
        return ChatSearchResponse(
            summary=response,
            stores=[],  # TODO: Integrate with actual search logic
            total_found=0,
        )

    except Exception as e:
        logger.error(f"Chat search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat search failed: {str(e)}",
        )
