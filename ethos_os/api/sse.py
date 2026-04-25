"""SSE endpoints for real-time dashboard updates."""

import asyncio
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ethos_os.db import get_session

router = APIRouter(prefix="/events", tags=["sse"])


class SSEEvent(BaseModel):
    """SSE event."""

    event: str
    data: dict


async def event_generator() -> AsyncGenerator[str, None]:
    """Generate SSE events."""
    import json
    
    last_heartbeat_count = 0
    last_pending_gates = 0
    
    while True:
        with get_session() as session:
            from ethos_os.execution.heartbeat import Heartbeat
            from ethos_os.models.gate import GateRequest
            
            heartbeat_count = session.query(Heartbeat).count()
            pending_gates = session.query(GateRequest).filter_by(status="pending").count()
            
            if heartbeat_count != last_heartbeat_count:
                yield f"event: heartbeat\ndata: {json.dumps({'count': heartbeat_count})}\n\n"
                last_heartbeat_count = heartbeat_count
            
            if pending_gates != last_pending_gates:
                yield f"event: gates\ndata: {json.dumps({'pending': pending_gates})}\n\n"
                last_pending_gates = pending_gates
        
        await asyncio.sleep(5)


@router.get("/stream")
async def sse_stream():
    """Server-Sent Events stream for real-time updates."""
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.get("/heartbeats/stream")
async def heartbeat_stream():
    """SSE stream for heartbeat updates."""
    import json
    from ethos_os.execution.heartbeat import Heartbeat
    
    async def gen():
        last_count = 0
        while True:
            with get_session() as session:
                count = session.query(Heartbeat).count()
                if count != last_count:
                    yield f"event: heartbeats\ndata: {json.dumps({'count': count})}\n\n"
                    last_count = count
            await asyncio.sleep(5)
    
    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
    )


@router.get("/gates/stream")
async def gates_stream():
    """SSE stream for gate status updates."""
    import json
    from ethos_os.models.gate import GateRequest
    
    async def gen():
        last_count = 0
        while True:
            with get_session() as session:
                count = session.query(GateRequest).filter_by(status="pending").count()
                if count != last_count:
                    yield f"event: gates\ndata: {json.dumps({'pending': count})}\n\n"
                    last_count = count
            await asyncio.sleep(5)
    
    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
    )