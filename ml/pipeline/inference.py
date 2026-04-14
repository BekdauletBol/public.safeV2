import asyncio
import time
from typing import Dict, Optional
import numpy as np
from loguru import logger

from ml.pipeline.detector import YOLODetector, SimpleTracker, Detection, apply_roi_filter, draw_detections
from app.core.config import settings


class CameraInferenceWorker:
    """Runs ML inference on a single camera stream."""

    def __init__(
        self,
        camera_id: int,
        detector: YOLODetector,
        stream_manager,
        db_session_factory,
        ws_manager,
        roi: Optional[tuple] = None,
        target_fps: int = 5,
    ):
        self.camera_id = camera_id
        self.detector = detector
        self.tracker = SimpleTracker(max_age=30, min_hits=3)
        self.stream_manager = stream_manager
        self.db_session_factory = db_session_factory
        self.ws_manager = ws_manager
        self.roi = roi
        self.target_fps = target_fps
        self._running = False
        self._last_count = 0
        self._frame_interval = 1.0 / target_fps

    async def start(self):
        self._running = True
        logger.info(f"Inference worker started for camera {self.camera_id}")
        while self._running:
            t0 = time.monotonic()
            await self._process_frame()
            elapsed = time.monotonic() - t0
            sleep_time = max(0, self._frame_interval - elapsed)
            await asyncio.sleep(sleep_time)

    def stop(self):
        self._running = False

    async def _process_frame(self):
        frame = self.stream_manager.get_frame(self.camera_id)
        if frame is None:
            return

        h, w = frame.shape[:2]

        # Run YOLO in executor to avoid blocking
        loop = asyncio.get_event_loop()
        detections = await loop.run_in_executor(None, self.detector.detect, frame)

        # Apply ROI filter
        if self.roi and self.roi[2] < 1.0 and self.roi[3] < 1.0:
            detections = apply_roi_filter(detections, self.roi, w, h)

        # Update tracker
        tracks = self.tracker.update(detections)
        count = len(tracks)

        if count != self._last_count:
            self._last_count = count
            await self._record_count(count)
            await self._broadcast(count)

    async def _record_count(self, count: int):
        try:
            async with self.db_session_factory() as db:
                from app.services.analytics_service import AnalyticsService
                await AnalyticsService.record_count(db, self.camera_id, count)
        except Exception as e:
            logger.error(f"Failed to record count for camera {self.camera_id}: {e}")

    async def _broadcast(self, count: int):
        try:
            await self.ws_manager.broadcast_camera_update(
                self.camera_id,
                {"people_count": count, "camera_id": self.camera_id},
            )
        except Exception as e:
            logger.error(f"Failed to broadcast for camera {self.camera_id}: {e}")


class InferenceOrchestrator:
    """Manages inference workers for all cameras."""

    def __init__(self, stream_manager, db_session_factory, ws_manager):
        self.stream_manager = stream_manager
        self.db_session_factory = db_session_factory
        self.ws_manager = ws_manager
        self.detector = YOLODetector(
            model_path=settings.MODEL_PATH,
            device=settings.INFERENCE_DEVICE,
            conf=settings.CONFIDENCE_THRESHOLD,
            iou_threshold=settings.IOU_THRESHOLD,
        )
        self.workers: Dict[int, CameraInferenceWorker] = {}
        self._tasks: Dict[int, asyncio.Task] = {}

    async def start(self):
        self.detector.load()
        logger.info("InferenceOrchestrator started")

    async def add_camera(self, camera_id: int, roi: Optional[tuple] = None):
        if camera_id in self.workers:
            await self.remove_camera(camera_id)

        worker = CameraInferenceWorker(
            camera_id=camera_id,
            detector=self.detector,
            stream_manager=self.stream_manager,
            db_session_factory=self.db_session_factory,
            ws_manager=self.ws_manager,
            roi=roi,
        )
        self.workers[camera_id] = worker
        self._tasks[camera_id] = asyncio.create_task(worker.start())
        logger.info(f"Inference worker added for camera {camera_id}")

    async def remove_camera(self, camera_id: int):
        if camera_id in self.workers:
            self.workers[camera_id].stop()
            del self.workers[camera_id]
        if camera_id in self._tasks:
            self._tasks[camera_id].cancel()
            del self._tasks[camera_id]

    async def update_roi(self, camera_id: int, roi: tuple):
        if camera_id in self.workers:
            self.workers[camera_id].roi = roi

    async def stop_all(self):
        for cam_id in list(self.workers.keys()):
            await self.remove_camera(cam_id)
