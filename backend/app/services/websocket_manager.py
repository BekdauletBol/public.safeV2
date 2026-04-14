import asyncio
import json
from typing import Dict, Set
from fastapi import WebSocket
from loguru import logger
from datetime import datetime


class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.camera_subscribers: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        for cam_id in list(self.camera_subscribers.keys()):
            self.camera_subscribers[cam_id].discard(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def subscribe_camera(self, websocket: WebSocket, camera_id: int):
        if camera_id not in self.camera_subscribers:
            self.camera_subscribers[camera_id] = set()
        self.camera_subscribers[camera_id].add(websocket)

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        data = json.dumps(message, default=str)
        dead = set()
        for ws in list(self.active_connections):
            try:
                await ws.send_text(data)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.disconnect(ws)

    async def broadcast_camera_update(self, camera_id: int, data: dict):
        message = {"type": "camera_update", "camera_id": camera_id, "data": data, "timestamp": datetime.utcnow().isoformat()}
        await self.broadcast(message)

    async def broadcast_system_update(self, data: dict):
        message = {"type": "system_update", "data": data, "timestamp": datetime.utcnow().isoformat()}
        await self.broadcast(message)


manager = ConnectionManager()
