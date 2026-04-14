from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(255), nullable=False)
    stream_url = Column(Text, nullable=False)
    address = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    is_connected = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    fps = Column(Integer, default=15)
    resolution_width = Column(Integer, default=1280)
    resolution_height = Column(Integer, default=720)

    analytics = relationship("AnalyticsRecord", back_populates="camera", cascade="all, delete-orphan")
    roi = relationship("ROIConfig", back_populates="camera", uselist=False, cascade="all, delete-orphan")
