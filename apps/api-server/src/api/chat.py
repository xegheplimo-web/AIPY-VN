from fastapi import APIRouter, WebSocket

router = APIRouter(prefix="/api", tags=["Chat"])


@router.get("/stores/{store_id}/messages")
async def get_store_messages(store_id: str):
    return {"messages": []}


@router.post("/messages")
async def send_message(msg: dict):
    return {"id": "msg_new", "status": "sent"}


@router.websocket("/ws/chat/{store_id}")
async def websocket_chat(websocket: WebSocket, store_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except:
        pass
