from fastapi import APIRouter, WebSocket, status
from pydantic import TypeAdapter, ValidationError
from starlette.websockets import WebSocketDisconnect

from app.core.security import InvalidTokenError, decode_jwt
from app.schemas.messages import ClientMessage

router = APIRouter(tags=["websocket"])
client_message_adapter: TypeAdapter[ClientMessage] = TypeAdapter(ClientMessage)


@router.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket, token: str | None = None) -> None:
    if token is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return 
    
    try:
        decode_jwt(token)
    except InvalidTokenError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    await websocket.accept()
    
    try:
        while True:
            payload = await websocket.receive_json()

            try:
                client_message_adapter.validate_python(payload)
            except ValidationError:
                await websocket.send_json(
                    {
                        "type": "error",
                        "reason": "malformed_payload"
                    }
                )

    except WebSocketDisconnect:
        return