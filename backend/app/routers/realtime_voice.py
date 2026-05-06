from typing import Optional

from fastapi import APIRouter, Query, WebSocket
from starlette.websockets import WebSocketDisconnect

from app.services.firebase_service import FirebaseService
from app.services.realtime_session_manager import realtime_session_manager

router = APIRouter(prefix="/api/realtime-voice", tags=["realtime-voice"])


async def get_websocket_user_id(websocket: WebSocket, token: Optional[str]) -> str:
    auth_header = websocket.headers.get("authorization")
    bearer_token = token
    if auth_header and auth_header.startswith("Bearer "):
        bearer_token = auth_header[7:]

    if not bearer_token:
        await websocket.close(code=1008)
        raise WebSocketDisconnect(code=1008)

    decoded = FirebaseService().verify_token(bearer_token)
    if not decoded:
        await websocket.close(code=1008)
        raise WebSocketDisconnect(code=1008)

    user_id = decoded.get("uid")
    if not user_id:
        await websocket.close(code=1008)
        raise WebSocketDisconnect(code=1008)
    return user_id


@router.websocket("/ws")
async def realtime_voice_ws(
    websocket: WebSocket,
    character_id: str = Query(...),
    session_id: Optional[str] = Query(None),
    token: Optional[str] = Query(None),
) -> None:
    user_id = await get_websocket_user_id(websocket, token)
    await realtime_session_manager.handle_client(
        websocket,
        user_id=user_id,
        character_id=character_id,
        session_id=session_id,
    )
