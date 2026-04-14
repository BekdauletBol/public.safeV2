import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
from loguru import logger
from datetime import datetime

from app.services.websocket_manager import manager
from app.services.analytics_service import AnalyticsService
from app.db.session import AsyncSessionLocal

router = APIRouter()


@router.websocket("/live")
async def websocket_live(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial camera counts
        async with AsyncSessionLocal() as db:
            counts = await AnalyticsService.get_realtime_counts(db)
            await websocket.send_json({
                "type": "initial_counts",
                "counts": counts,
                "timestamp": datetime.utcnow().isoformat(),
            })

        # Periodic updates loop
        async def push_updates():
            while True:
                async with AsyncSessionLocal() as db:
                    counts = await AnalyticsService.get_realtime_counts(db)
                await websocket.send_json({
                    "type": "count_update",
                    "counts": counts,
                    "timestamp": datetime.utcnow().isoformat(),
                })
                await asyncio.sleep(3)

        update_task = asyncio.create_task(push_updates())

        # Listen for client messages
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60)
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif msg.get("type") == "subscribe_camera":
                    await manager.subscribe_camera(websocket, msg["camera_id"])
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        update_task.cancel()
        manager.disconnect(websocket)
