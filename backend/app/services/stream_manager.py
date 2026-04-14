import asyncio
import cv2
import numpy as np
from typing import Dict, Optional, AsyncGenerator
from loguru import logger
from datetime import datetime
import threading
import queue

from app.core.config import settings


class CameraStream:
    def __init__(self, camera_id: int, stream_url: str):
        self.camera_id = camera_id
        self.stream_url = stream_url
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self.retry_count = 0
        self.last_frame: Optional[np.ndarray] = None
        self.last_frame_time: Optional[datetime] = None
        self.frame_queue: queue.Queue = queue.Queue(maxsize=settings.STREAM_BUFFER_SIZE)
        self._thread: Optional[threading.Thread] = None
        self.is_connected = False

    def _capture_loop(self):
        while self.is_running:
            if self.cap is None or not self.cap.isOpened():
                self._connect()
                if not self.is_connected:
                    logger.warning(f"Camera {self.camera_id}: reconnect failed, waiting {settings.STREAM_RECONNECT_DELAY}s")
                    asyncio.run(asyncio.sleep(settings.STREAM_RECONNECT_DELAY))
                    continue

            ret, frame = self.cap.read()
            if ret:
                self.retry_count = 0
                self.last_frame = frame
                self.last_frame_time = datetime.utcnow()
                try:
                    if self.frame_queue.full():
                        self.frame_queue.get_nowait()
                    self.frame_queue.put_nowait(frame)
                except queue.Full:
                    pass
            else:
                logger.warning(f"Camera {self.camera_id}: failed to read frame")
                self.is_connected = False
                self.cap.release()
                self.cap = None
                self.retry_count += 1
                if self.retry_count >= settings.STREAM_MAX_RETRIES:
                    logger.error(f"Camera {self.camera_id}: max retries reached, stopping")
                    self.is_running = False

    def _connect(self):
        try:
            logger.info(f"Camera {self.camera_id}: connecting to {self.stream_url}")
            if self.cap:
                self.cap.release()

            # Handle different stream types
            if self.stream_url.startswith("rtsp://"):
                self.cap = cv2.VideoCapture(self.stream_url, cv2.CAP_FFMPEG)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            elif self.stream_url.startswith("http"):
                self.cap = cv2.VideoCapture(self.stream_url)
            elif self.stream_url.isdigit():
                self.cap = cv2.VideoCapture(int(self.stream_url))
            else:
                self.cap = cv2.VideoCapture(self.stream_url)

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

            if self.cap.isOpened():
                self.is_connected = True
                logger.info(f"Camera {self.camera_id}: connected successfully")
            else:
                self.is_connected = False
                logger.error(f"Camera {self.camera_id}: failed to open stream")
        except Exception as e:
            logger.error(f"Camera {self.camera_id}: connection error: {e}")
            self.is_connected = False

    def start(self):
        self.is_running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        logger.info(f"Camera {self.camera_id}: stream started")

    def stop(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
        logger.info(f"Camera {self.camera_id}: stream stopped")

    def get_frame(self) -> Optional[np.ndarray]:
        try:
            return self.frame_queue.get_nowait()
        except queue.Empty:
            return self.last_frame

    def get_jpeg_frame(self) -> Optional[bytes]:
        frame = self.get_frame()
        if frame is None:
            return None
        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return buffer.tobytes()


class StreamManager:
    def __init__(self):
        self.streams: Dict[int, CameraStream] = {}
        self._lock = asyncio.Lock()

    async def start_all_streams(self):
        from app.db.session import AsyncSessionLocal
        from app.models.camera import Camera
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Camera).where(Camera.is_active == True))
            cameras = result.scalars().all()
            for camera in cameras:
                await self.add_stream(camera.id, camera.stream_url)

    async def stop_all_streams(self):
        for stream in self.streams.values():
            stream.stop()
        self.streams.clear()

    async def add_stream(self, camera_id: int, stream_url: str):
        async with self._lock:
            if camera_id in self.streams:
                self.streams[camera_id].stop()
            stream = CameraStream(camera_id, stream_url)
            stream.start()
            self.streams[camera_id] = stream
            logger.info(f"StreamManager: added stream for camera {camera_id}")

    async def remove_stream(self, camera_id: int):
        async with self._lock:
            if camera_id in self.streams:
                self.streams[camera_id].stop()
                del self.streams[camera_id]

    def get_stream(self, camera_id: int) -> Optional[CameraStream]:
        return self.streams.get(camera_id)

    def get_frame(self, camera_id: int) -> Optional[np.ndarray]:
        stream = self.get_stream(camera_id)
        if stream:
            return stream.get_frame()
        return None

    def get_status(self) -> Dict:
        return {
            cam_id: {
                "is_connected": stream.is_connected,
                "is_running": stream.is_running,
                "retry_count": stream.retry_count,
                "last_frame_time": stream.last_frame_time.isoformat() if stream.last_frame_time else None,
            }
            for cam_id, stream in self.streams.items()
        }

    async def stream_mjpeg(self, camera_id: int) -> AsyncGenerator[bytes, None]:
        stream = self.get_stream(camera_id)
        if not stream:
            return

        while stream.is_running:
            frame_bytes = stream.get_jpeg_frame()
            if frame_bytes:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                )
            await asyncio.sleep(1 / 30)
