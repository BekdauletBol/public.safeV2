from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.roi import ROIConfig
from app.schemas.analytics import ROISchema
from app.core.security import get_current_user

router = APIRouter()


@router.get("/{camera_id}", response_model=ROISchema)
async def get_roi(camera_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ROIConfig).where(ROIConfig.camera_id == camera_id))
    roi = result.scalar_one_or_none()
    if not roi:
        return ROISchema(camera_id=camera_id, x=0.0, y=0.0, width=1.0, height=1.0, is_active=False)
    return roi


@router.post("/{camera_id}", response_model=ROISchema)
async def set_roi(
    camera_id: int,
    roi_in: ROISchema,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    result = await db.execute(select(ROIConfig).where(ROIConfig.camera_id == camera_id))
    existing = result.scalar_one_or_none()

    if existing:
        existing.x = roi_in.x
        existing.y = roi_in.y
        existing.width = roi_in.width
        existing.height = roi_in.height
        existing.is_active = roi_in.is_active
        roi = existing
    else:
        roi = ROIConfig(
            camera_id=camera_id,
            x=roi_in.x,
            y=roi_in.y,
            width=roi_in.width,
            height=roi_in.height,
            is_active=roi_in.is_active,
        )
        db.add(roi)

    await db.commit()
    await db.refresh(roi)
    return roi


@router.delete("/{camera_id}", status_code=204)
async def delete_roi(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    result = await db.execute(select(ROIConfig).where(ROIConfig.camera_id == camera_id))
    roi = result.scalar_one_or_none()
    if roi:
        await db.delete(roi)
        await db.commit()
