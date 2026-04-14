from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.session import get_db
from app.models.camera import Camera
from app.schemas.camera import CameraCreate, CameraUpdate, CameraOut
from app.core.security import get_current_user
from app.services.websocket_manager import manager

router = APIRouter()


@router.get("/", response_model=List[CameraOut])
async def list_cameras(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Camera).order_by(Camera.id))
    cameras = result.scalars().all()
    return cameras


@router.get("/{camera_id}", response_model=CameraOut)
async def get_camera(camera_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return camera


@router.post("/", response_model=CameraOut, status_code=201)
async def create_camera(
    camera_in: CameraCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    camera = Camera(**camera_in.model_dump())
    db.add(camera)
    await db.commit()
    await db.refresh(camera)

    # Start stream immediately
    stream_manager = request.app.state.stream_manager
    await stream_manager.add_stream(camera.id, camera.stream_url)

    # Notify all WS clients
    await manager.broadcast({
        "type": "camera_added",
        "camera": {
            "id": camera.id,
            "name": camera.name,
            "address": camera.address,
            "stream_url": camera.stream_url,
            "is_active": camera.is_active,
            "is_connected": camera.is_connected,
            "current_count": 0,
        }
    })

    return camera


@router.put("/{camera_id}", response_model=CameraOut)
async def update_camera(
    camera_id: int,
    camera_in: CameraUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    update_data = camera_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(camera, field, value)

    await db.commit()
    await db.refresh(camera)

    # Restart stream if URL changed
    if "stream_url" in update_data:
        stream_manager = request.app.state.stream_manager
        await stream_manager.add_stream(camera.id, camera.stream_url)

    await manager.broadcast({"type": "camera_updated", "camera_id": camera_id})
    return camera


@router.delete("/{camera_id}", status_code=204)
async def delete_camera(
    camera_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    stream_manager = request.app.state.stream_manager
    await stream_manager.remove_stream(camera_id)

    await db.delete(camera)
    await db.commit()

    await manager.broadcast({"type": "camera_removed", "camera_id": camera_id})
