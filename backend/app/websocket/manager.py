import asyncio
from typing import Dict, Set

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.lock = asyncio.Lock()

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        async with self.lock:
            conns = self.active_connections.setdefault(session_id, set())
            conns.add(websocket)

    async def disconnect(self, session_id: str, websocket: WebSocket):
        async with self.lock:
            conns = self.active_connections.get(session_id)
            if conns and websocket in conns:
                conns.remove(websocket)
            if conns and len(conns) == 0:
                self.active_connections.pop(session_id, None)

    async def broadcast(self, session_id: str, message: dict):
        conns = self.active_connections.get(session_id, set())
        for ws in list(conns):
            try:
                await ws.send_json(message)
            except Exception:
                await self.disconnect(session_id, ws)

manager = ConnectionManager()
