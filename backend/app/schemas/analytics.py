from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class AnalyticsPoint(BaseModel):
    timestamp: datetime
    people_count: int
    camera_id: int


class HourlyData(BaseModel):
    hour: int
    total: int
    avg: float
    max: int


class DailyData(BaseModel):
    date: str
    total: int
    avg: float
    peak_hour: Optional[int]


class CameraAnalytics(BaseModel):
    camera_id: int
    camera_name: str
    address: str
    hourly: List[HourlyData]
    daily: List[DailyData]
    total_count: int
    avg_count: float
    peak_hour: Optional[int]


class SystemAnalytics(BaseModel):
    total_cameras: int
    active_cameras: int
    total_people_today: int
    peak_hour_today: Optional[int]
    cameras: List[CameraAnalytics]


class ROISchema(BaseModel):
    camera_id: int
    x: float
    y: float
    width: float
    height: float
    is_active: bool = True

    class Config:
        from_attributes = True
