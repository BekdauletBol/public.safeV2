from pydantic import BaseModel, HttpUrl, validator
from typing import Optional
from datetime import datetime


class CameraBase(BaseModel):
    name: str
    stream_url: str
    address: str
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    fps: int = 15
    resolution_width: int = 1280
    resolution_height: int = 720


class CameraCreate(CameraBase):
    pass


class CameraUpdate(BaseModel):
    name: Optional[str] = None
    stream_url: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    fps: Optional[int] = None


class CameraOut(CameraBase):
    id: int
    is_active: bool
    is_connected: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    current_count: Optional[int] = 0

    class Config:
        from_attributes = True


class CameraStatusUpdate(BaseModel):
    camera_id: int
    is_connected: bool
    people_count: int
    timestamp: datetime
