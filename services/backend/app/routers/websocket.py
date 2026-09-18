import uuid
from datetime import UTC, datetime
from time import perf_counter_ns

from fastapi import APIRouter, WebSocket, status
from pydantic import TypeAdapter, ValidationError
from starlette.websockets import WebSocketDisconnect, WebSocketState

from app.core.security import InvalidTokenError, decode_jwt
from app.schemas.auth import TokenPayload
from app.schemas.messages import ClientMessage
from app.services.chat import ConnectionLimitReachedError
from app.services.translation.diagnostics import elapsed_ms

router = APIRouter(tags=["websocket"])
client_message_adapter: TypeAdapter[ClientMessage] = TypeAdapter(ClientMessage)


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

    chat = websocket.app.state.chat_service
    connection = None

    try:
        await websocket.accept()
        connection = await chat.connect(
            websocket, nickname=token_payload.nickname, language=token_payload.language
        )
        await chat.join_room(connection, room="general")
        await chat.broadcast_room_presence(room="general")

        while True:
            payload = await websocket.receive_json()
            message_received_ns = perf_counter_ns()

            try:
                validation_started_ns = perf_counter_ns()
                validated: ClientMessage = client_message_adapter.validate_python(payload)
                validation_ms = elapsed_ms(validation_started_ns)
                now = datetime.now(UTC)
                date_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")
                if validated.type == "room_message":
                    await chat.send_room_message(
                        connection,
                        text=validated.text,
                        message_id=str(uuid.uuid4()),
                        sent_at=date_str,
                        message_received_ns=message_received_ns,
                        validation_ms=validation_ms,
                    )
                if validated.type == "private_message":
                    await chat.send_private_message(
                        connection,
                        recipient_nickname=validated.recipient_nickname,
                        text=validated.text,
                        message_id=str(uuid.uuid4()),
                        sent_at=date_str,
                        message_received_ns=message_received_ns,
                        validation_ms=validation_ms,
                    )

            except ValidationError:
                await websocket.send_json({"type": "error", "reason": "malformed_payload"})

    except ConnectionLimitReachedError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    except WebSocketDisconnect:
        if connection is not None:
            await chat.disconnect(connection)
            await chat.broadcast_room_presence(room="general")
    except RuntimeError:
        if (
            websocket.client_state is WebSocketState.CONNECTED
            and websocket.application_state is WebSocketState.CONNECTED
        ):
            raise
        if connection is not None:
            await chat.disconnect(connection)
            await chat.broadcast_room_presence(room="general")
