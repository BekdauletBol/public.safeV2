from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter()


@router.get("/{camera_id}/feed")
async def stream_feed(camera_id: int, request: Request):
    stream_manager = request.app.state.stream_manager
    stream = stream_manager.get_stream(camera_id)
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found for this camera")

    async def generate():
        async for chunk in stream_manager.stream_mjpeg(camera_id):
            if await request.is_disconnected():
                break
            yield chunk

    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/{camera_id}/snapshot")
async def snapshot(camera_id: int, request: Request):
    stream_manager = request.app.state.stream_manager
    stream = stream_manager.get_stream(camera_id)
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")

    frame_bytes = stream.get_jpeg_frame()
    if not frame_bytes:
        raise HTTPException(status_code=503, detail="No frame available")

    return StreamingResponse(iter([frame_bytes]), media_type="image/jpeg")


@router.get("/status")
async def streams_status(request: Request):
    stream_manager = request.app.state.stream_manager
    return stream_manager.get_status()
