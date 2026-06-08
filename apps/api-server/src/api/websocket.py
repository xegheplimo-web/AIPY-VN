"""
WebSocket endpoints for real-time features
"""

import json
import uuid
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import UUID

from src.database import async_session
from src.models.user import User
from src.models.chat import Message as ChatMessage
from src.middleware.auth_middleware import get_current_user

router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        # Store active connections: {user_id: {connection_id: websocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # Store room subscriptions: {room_id: {user_id}}
        self.rooms: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept a new connection"""
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
        
        self.active_connections[user_id][connection_id] = websocket
        return connection_id
    
    def disconnect(self, user_id: str, connection_id: str):
        """Remove a connection"""
        if user_id in self.active_connections:
            if connection_id in self.active_connections[user_id]:
                del self.active_connections[user_id][connection_id]
            
            # Clean up empty user entries
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to specific user"""
        if user_id in self.active_connections:
            for connection_id, websocket in self.active_connections[user_id].items():
                try:
                    await websocket.send_json(message)
                except Exception:
                    # Remove broken connection
                    self.disconnect(user_id, connection_id)
    
    async def broadcast_to_room(self, message: dict, room_id: str):
        """Broadcast message to all users in a room"""
        if room_id in self.rooms:
            for user_id in self.rooms[room_id]:
                await self.send_personal_message(message, user_id)
    
    def join_room(self, user_id: str, room_id: str):
        """Add user to a room"""
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        self.rooms[room_id].add(user_id)
    
    def leave_room(self, user_id: str, room_id: str):
        """Remove user from a room"""
        if room_id in self.rooms:
            self.rooms[room_id].discard(user_id)
            
            # Clean up empty rooms
            if not self.rooms[room_id]:
                del self.rooms[room_id]


manager = ConnectionManager()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """Main WebSocket endpoint for real-time updates"""
    connection_id = await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Handle different message types
            message_type = data.get("type")
            
            if message_type == "join_room":
                room_id = data.get("room_id")
                manager.join_room(user_id, room_id)
                await websocket.send_json({
                    "type": "room_joined",
                    "room_id": room_id,
                })
            
            elif message_type == "leave_room":
                room_id = data.get("room_id")
                manager.leave_room(user_id, room_id)
                await websocket.send_json({
                    "type": "room_left",
                    "room_id": room_id,
                })
            
            elif message_type == "chat_message":
                # Handle chat message
                room_id = data.get("room_id")
                content = data.get("content")
                
                # Save to database
                async with async_session() as session:
                    message = ChatMessage(
                        id=uuid.uuid4(),
                        sender_id=UUID(user_id),
                        receiver_id=UUID(data.get("receiver_id")),
                        content=content,
                        is_read=False,
                    )
                    session.add(message)
                    await session.commit()
                    await session.refresh(message)
                    
                    # Broadcast to room
                    await manager.broadcast_to_room({
                        "type": "new_message",
                        "message": {
                            "id": str(message.id),
                            "sender_id": str(message.sender_id),
                            "receiver_id": str(message.receiver_id),
                            "content": message.content,
                            "created_at": message.created_at,
                        }
                    }, room_id)
            
            elif message_type == "typing":
                # Broadcast typing indicator
                room_id = data.get("room_id")
                await manager.broadcast_to_room({
                    "type": "typing",
                    "user_id": user_id,
                    "room_id": room_id,
                }, room_id)
            
            elif message_type == "ping":
                # Respond to ping
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        manager.disconnect(user_id, connection_id)
        # Remove user from all rooms
        for room_id in list(manager.rooms.keys()):
            manager.leave_room(user_id, room_id)


@router.websocket("/ws/chat/{room_id}")
async def chat_websocket(websocket: WebSocket, room_id: str):
    """WebSocket endpoint for chat rooms"""
    # Extract user_id from query params (in production, validate with JWT)
    from fastapi import Query
    user_id = Query(..., alias="user_id")
    
    connection_id = await manager.connect(websocket, user_id)
    manager.join_room(user_id, room_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Handle chat messages
            if data.get("type") == "message":
                content = data.get("content")
                receiver_id = data.get("receiver_id")
                
                # Save to database
                async with async_session() as session:
                    message = ChatMessage(
                        id=uuid.uuid4(),
                        sender_id=UUID(user_id),
                        receiver_id=UUID(receiver_id),
                        content=content,
                        is_read=False,
                    )
                    session.add(message)
                    await session.commit()
                    await session.refresh(message)
                    
                    # Broadcast to room
                    await manager.broadcast_to_room({
                        "type": "new_message",
                        "message": {
                            "id": str(message.id),
                            "sender_id": str(message.sender_id),
                            "receiver_id": str(message.receiver_id),
                            "content": message.content,
                            "created_at": message.created_at,
                        }
                    }, room_id)
    
    except WebSocketDisconnect:
        manager.disconnect(user_id, connection_id)
        manager.leave_room(user_id, room_id)
