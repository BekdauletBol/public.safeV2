"""
Adaptive inference load control.
Dynamically adjusts FPS per camera based on system load and traffic patterns.
"""
import psutil
import asyncio
from typing import Dict
from loguru import logger


class AdaptiveLoadController:
    def __init__(self, orchestrator, max_cpu_pct: float = 80.0):
        self.orchestrator = orchestrator
        self.max_cpu_pct = max_cpu_pct
        self._running = False

    async def start(self):
        self._running = True
        while self._running:
            await self._adjust()
            await asyncio.sleep(10)

    def stop(self):
        self._running = False

    async def _adjust(self):
        cpu = psutil.cpu_percent(interval=1)
        if cpu > self.max_cpu_pct:
            # Reduce FPS on all workers
            for worker in self.orchestrator.workers.values():
                if worker.target_fps > 1:
                    worker.target_fps = max(1, worker.target_fps - 1)
                    worker._frame_interval = 1.0 / worker.target_fps
            logger.warning(f"CPU {cpu:.1f}% — reduced inference FPS")
        elif cpu < self.max_cpu_pct * 0.6:
            # Restore FPS
            for worker in self.orchestrator.workers.values():
                if worker.target_fps < 10:
                    worker.target_fps = min(10, worker.target_fps + 1)
                    worker._frame_interval = 1.0 / worker.target_fps
