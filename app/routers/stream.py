import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.firestore.live_board import get_showtime_board


router = APIRouter(
    prefix="/api/v1/stream",
    tags=["Stream"],
)


@router.get("/showtimes/{showtime_id}")
async def stream_showtime(showtime_id: int):
    async def event_generator():
        last_data = None

        while True:
            data = get_showtime_board(showtime_id)

            if data is None:
                yield "event: error\ndata: Showtime not found\n\n"
                break

            current_data = json.dumps(data, sort_keys=True)

            if current_data != last_data:
                yield f"event: showtime_update\ndata: {current_data}\n\n"
                last_data = current_data

            await asyncio.sleep(2)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )