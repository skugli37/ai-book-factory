from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException # pyre-ignore[21]
from app.websocket.manager import manager # pyre-ignore[21]
from app.api.auth import get_me # pyre-ignore[21]
from sqlalchemy.orm import Session # pyre-ignore[21]
from app.core.database import get_db # pyre-ignore[21]

async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await manager.connect(job_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(job_id)
    except Exception:
        manager.disconnect(job_id)
