import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import init_db
from app.api.routes import cameras, streams, analytics, reports, auth, roi, websocket
from app.services.stream_manager import StreamManager
from app.workers.scheduler import start_scheduler

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    stream_manager = StreamManager()
    app.state.stream_manager = stream_manager
    await stream_manager.start_all_streams()
    scheduler_task = asyncio.create_task(start_scheduler())
    yield
    await stream_manager.stop_all_streams()
    scheduler_task.cancel()


app = FastAPI(
    title="public.safeV3",
    description="Real-time AI-powered video surveillance and people counting system",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(settings.REPORTS_DIR, exist_ok=True)
app.mount("/reports", StaticFiles(directory=settings.REPORTS_DIR), name="reports")

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(cameras.router, prefix="/api/cameras", tags=["cameras"])
app.include_router(streams.router, prefix="/api/streams", tags=["streams"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(roi.router, prefix="/api/roi", tags=["roi"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "3.0.0"}
