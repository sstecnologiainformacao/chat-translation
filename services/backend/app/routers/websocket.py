import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, WebSocket, status
from pydantic import TypeAdapter, ValidationError
from starlette.websockets import WebSocketDisconnect

from app.core.security import InvalidTokenError, decode_jwt
from app.schemas.auth import TokenPayload
from app.schemas.messages import ClientMessage
from app.services.chat import ChatService, ConnectionManager
from app.services.translation.base import FakeTranslator

router = APIRouter(tags=["websocket"])
client_message_adapter: TypeAdapter[ClientMessage] = TypeAdapter(ClientMessage)
chat = ChatService(ConnectionManager(max_connections=10), FakeTranslator())


@router.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket, token: str | None = None) -> None:
    if token is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return 
    
    try:
        token_payload: TokenPayload = decode_jwt(token)
    except InvalidTokenError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    await websocket.accept()
    connection = await chat.connect(
        websocket,
        nickname=token_payload.nickname,
        language=token_payload.language
    )
    await chat.join_room(
        connection,
        room="general"
    )
    
    try:
        while True:
            payload = await websocket.receive_json()

            try:
                validated: ClientMessage = client_message_adapter.validate_python(
                    payload
                )
                now = datetime.now(UTC)
                date_str = now.strftime('%Y-%m-%dT%H:%M:%SZ')
                if validated.type == "room_message":
                    await chat.send_room_message(
                        connection,
                        text=validated.text,
                        message_id=str(uuid.uuid4()),
                        sent_at=date_str
                    )
                if validated.type == "private_message":
                    await chat.send_private_message(
                        connection,
                        recipient_nickname=validated.recipient_nickname,
                        text=validated.text,
                        message_id=str(uuid.uuid4()),
                        sent_at=date_str
                    )

            except ValidationError:
                await websocket.send_json(
                    {
                        "type": "error",
                        "reason": "malformed_payload"
                    }
                )

    except WebSocketDisconnect:
        await chat.disconnect(connection)
        return
