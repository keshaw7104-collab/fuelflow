import asyncio
import json
from typing import Set
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()

_clients: Set[asyncio.Queue] = set()


async def publish_payment(payment: dict):
    if not _clients:
        return

    message = f"data: {json.dumps(payment, default=str)}\n\n"

    for queue in list(_clients):
        try:
            queue.put_nowait(message)
        except Exception:
            _clients.discard(queue)


@router.get("/api/payments/stream")
async def payment_stream():
    queue = asyncio.Queue()
    _clients.add(queue)

    async def event_generator():
        try:
            yield "event: connected\ndata: {\"status\":\"connected\"}\n\n"

            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=20)
                    yield message
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
        finally:
            _clients.discard(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
