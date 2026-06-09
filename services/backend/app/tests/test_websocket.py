import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect


def test_websocket_rejects_missing_token(client: TestClient) -> None:
    with pytest.raises(WebSocketDisconnect) as disconnect:
        with client.websocket_connect("/ws/chat"):
            pass

    assert disconnect.value.code == 1008


def test_websocket_rejects_invalid_token(client: TestClient) -> None:
    with pytest.raises(WebSocketDisconnect) as disconnect:
        with client.websocket_connect("/ws/chat?token=not-a-real-token"):
            pass

    assert disconnect.value.code == 1008


def test_websocket_accepts_valid_token(client: TestClient) -> None:
    from app.core.security import encode_jwt

    token = encode_jwt(nickname="joao", language="Portuguese")

    with client.websocket_connect(f"/ws/chat?token={token}"):
        pass


def test_websocket_returns_error_for_malformed_payload(client: TestClient) -> None:
    from app.core.security import encode_jwt

    token = encode_jwt(nickname="joao", language="Portuguese")

    with client.websocket_connect(f"/ws/chat?token={token}") as websocket:
        websocket.send_json({ "type": "unknown" })
        message = websocket.receive_json()

    assert message == {
        "type": "error",
        "reason": "malformed_payload",
    }


def test_websocket_routes_room_message_chat_service(client: TestClient) -> None:
    from app.core.security import encode_jwt

    token = encode_jwt(nickname="joao", language="Portuguese")

    with client.websocket_connect(f"/ws/chat?token={token}") as websocket:
        websocket.send_json({
            "type": "room_message",
            "room": "general",
            "text": "Hello"
        })
        message = websocket.receive_json()

    assert message["type"] == "room_message"
    assert message["room"] == "general"
    assert message["sender_nickname"] == "joao"
    assert message["sender_language"] == "Portuguese"
    assert message["original_text"] == "Hello"
    assert message["translations"] == {}
    
    assert len(message["message_id"].strip())
    assert len(message["sent_at"].strip())


def test_websocket_routes_private_message_recipient_not_found(client: TestClient) -> None:
    from app.core.security import encode_jwt

    token = encode_jwt(nickname="joao", language="Portuguese")

    with client.websocket_connect(f"/ws/chat?token={token}") as websocket:
        websocket.send_json({
            "type": "private_message",
            "recipient_nickname": "maria",
            "text": "Hello",
        })
        message = websocket.receive_json()

    assert message == {
        "type": "error",
        "reason": "recipient_not_found",
    }
