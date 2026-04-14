import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass, field
from loguru import logger
import time


@dataclass
class Detection:
    bbox: Tuple[float, float, float, float]  # x1, y1, x2, y2
    confidence: float
    class_id: int = 0

    @property
    def center(self):
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    @property
    def area(self):
        x1, y1, x2, y2 = self.bbox
        return (x2 - x1) * (y2 - y1)


@dataclass
class Track:
    track_id: int
    bbox: Tuple[float, float, float, float]
    confidence: float
    age: int = 0
    hits: int = 1
    time_since_update: int = 0
    history: List = field(default_factory=list)

    @property
    def is_confirmed(self):
        return self.hits >= 3

    @property
    def center(self):
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)


def iou(box1, box2) -> float:
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - inter
    return inter / union if union > 0 else 0.0


class SimpleTracker:
    """Lightweight IoU-based tracker inspired by ByteTrack."""

    def __init__(self, max_age: int = 30, min_hits: int = 3, iou_threshold: float = 0.3):
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        self._next_id = 1
        self.tracks: List[Track] = []

    def update(self, detections: List[Detection]) -> List[Track]:
        # Increment age
        for t in self.tracks:
            t.time_since_update += 1

        if not detections:
            self.tracks = [t for t in self.tracks if t.time_since_update <= self.max_age]
            return [t for t in self.tracks if t.is_confirmed]

        if not self.tracks:
            for det in detections:
                self.tracks.append(Track(
                    track_id=self._next_id,
                    bbox=det.bbox,
                    confidence=det.confidence,
                ))
                self._next_id += 1
            return [t for t in self.tracks if t.is_confirmed]

        # Greedy IoU matching
        matched_track_ids = set()
        matched_det_ids = set()

        iou_matrix = np.zeros((len(self.tracks), len(detections)))
        for ti, track in enumerate(self.tracks):
            for di, det in enumerate(detections):
                iou_matrix[ti, di] = iou(track.bbox, det.bbox)

        # Sort by iou descending
        pairs = sorted(
            [(ti, di) for ti in range(len(self.tracks)) for di in range(len(detections))],
            key=lambda p: -iou_matrix[p[0], p[1]],
        )

        for ti, di in pairs:
            if ti in matched_track_ids or di in matched_det_ids:
                continue
            if iou_matrix[ti, di] >= self.iou_threshold:
                self.tracks[ti].bbox = detections[di].bbox
                self.tracks[ti].confidence = detections[di].confidence
                self.tracks[ti].hits += 1
                self.tracks[ti].time_since_update = 0
                self.tracks[ti].age += 1
                matched_track_ids.add(ti)
                matched_det_ids.add(di)

        # New tracks for unmatched detections
        for di, det in enumerate(detections):
            if di not in matched_det_ids:
                self.tracks.append(Track(
                    track_id=self._next_id,
                    bbox=det.bbox,
                    confidence=det.confidence,
                ))
                self._next_id += 1

        # Remove old tracks
        self.tracks = [t for t in self.tracks if t.time_since_update <= self.max_age]

        return [t for t in self.tracks if t.is_confirmed]


class YOLODetector:
    def __init__(self, model_path: str, device: str = "cpu", conf: float = 0.5, iou_threshold: float = 0.4):
        self.model_path = model_path
        self.device = device
        self.conf = conf
        self.iou_threshold = iou_threshold
        self.model = None
        self._loaded = False

    def load(self):
        try:
            from ultralytics import YOLO
            self.model = YOLO(self.model_path)
            self._loaded = True
            logger.info(f"YOLO model loaded: {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            self._loaded = False

    def detect(self, frame: np.ndarray) -> List[Detection]:
        if not self._loaded or self.model is None:
            return []

        try:
            results = self.model(
                frame,
                classes=[0],  # person class only
                conf=self.conf,
                iou=self.iou_threshold,
                verbose=False,
                device=self.device,
            )

            detections = []
            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    conf = float(box.conf[0])
                    detections.append(Detection(
                        bbox=(x1, y1, x2, y2),
                        confidence=conf,
                        class_id=0,
                    ))
            return detections
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return []


def apply_roi_filter(
    detections: List[Detection],
    roi: Tuple[float, float, float, float],
    frame_w: int,
    frame_h: int,
) -> List[Detection]:
    """Filter detections to only those within ROI (normalized coordinates)."""
    rx, ry, rw, rh = roi
    roi_x1 = rx * frame_w
    roi_y1 = ry * frame_h
    roi_x2 = (rx + rw) * frame_w
    roi_y2 = (ry + rh) * frame_h

    filtered = []
    for det in detections:
        cx, cy = det.center
        if roi_x1 <= cx <= roi_x2 and roi_y1 <= cy <= roi_y2:
            filtered.append(det)
    return filtered


def draw_detections(
    frame: np.ndarray,
    tracks: List[Track],
    count: int,
    roi: Optional[Tuple] = None,
) -> np.ndarray:
    h, w = frame.shape[:2]

    # Draw ROI
    if roi:
        rx, ry, rw, rh = roi
        x1 = int(rx * w)
        y1 = int(ry * h)
        x2 = int((rx + rw) * w)
        y2 = int((ry + rh) * h)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)

    # Draw tracks
    for track in tracks:
        bx1, by1, bx2, by2 = [int(v) for v in track.bbox]
        cv2.rectangle(frame, (bx1, by1), (bx2, by2), (0, 200, 0), 2)
        cv2.putText(
            frame, f"#{track.track_id}",
            (bx1, by1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0), 1,
        )

    # Count overlay
    cv2.rectangle(frame, (0, 0), (180, 40), (0, 0, 0), -1)
    cv2.putText(frame, f"Count: {count}", (8, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

    return frame
