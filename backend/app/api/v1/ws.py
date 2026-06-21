from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.websocket.manager import manager
from app.core.security import decode_token

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # expect ?token= or header; simplistic implementation
    token = websocket.query_params.get("token")
    payload = decode_token(token) if token else None
    session_id = websocket.query_params.get("session_id") or (payload and payload.get("sub"))
    if not session_id:
        await websocket.close(code=4001)
        return
    await manager.connect(session_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # handle incoming frame or control messages
            # For now, echo back an acknowledgement
            await manager.broadcast(session_id, {"type": "ack", "received": True})
    except WebSocketDisconnect:
        await manager.disconnect(session_id, websocket)
