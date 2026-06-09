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


def test_websocket_routes_private_message_both_receive_message(client: TestClient) -> None:
    from app.core.security import encode_jwt

    token_joao = encode_jwt(nickname="joao", language="Portuguese")
    token_maria = encode_jwt(nickname="maria", language="Portuguese")

    with client.websocket_connect(f"/ws/chat?token={token_joao}") as websocket_joao:
        with client.websocket_connect(f"/ws/chat?token={token_maria}") as websocket_maria:
            websocket_joao.send_json({
                "type": "private_message",
                "recipient_nickname": "maria",
                "text": "Hello",
            })
            message_joao = websocket_joao.receive_json()
            message_maria = websocket_maria.receive_json()

    assert message_joao["type"] == "private_message"
    assert message_joao["sender_nickname"] == "joao"
    assert message_joao["recipient_nickname"] == "maria"
    assert message_joao["sender_language"] == "Portuguese"
    assert message_joao["original_text"] == "Hello"
    assert message_joao["translations"] == {}
    assert len(message_joao["message_id"].strip())
    assert len(message_joao["sent_at"].strip())

    assert message_maria["type"] == "private_message"
    assert message_maria["sender_nickname"] == "joao"
    assert message_maria["recipient_nickname"] == "maria"
    assert message_maria["sender_language"] == "Portuguese"
    assert message_maria["original_text"] == "Hello"
    assert message_maria["translations"] == {}
    assert len(message_maria["message_id"].strip())
    assert len(message_maria["sent_at"].strip())


def test_websocket_routes_private_message_only_both_receive_message(client: TestClient) -> None:
    from app.core.security import encode_jwt

    token_joao = encode_jwt(nickname="joao", language="Portuguese")
    token_maria = encode_jwt(nickname="maria", language="Portuguese")
    token_ana = encode_jwt(nickname="ana", language="Portuguese")

    with client.websocket_connect(f"/ws/chat?token={token_joao}") as websocket_joao:
        with client.websocket_connect(f"/ws/chat?token={token_maria}") as websocket_maria:
            with client.websocket_connect(f"/ws/chat?token={token_ana}"):
                websocket_joao.send_json({
                    "type": "private_message",
                    "recipient_nickname": "maria",
                    "text": "Hello",
                })
                message_joao = websocket_joao.receive_json()
                message_maria = websocket_maria.receive_json()

    assert message_joao["type"] == "private_message"
    assert message_joao["sender_nickname"] == "joao"
    assert message_joao["recipient_nickname"] == "maria"
    assert message_joao["sender_language"] == "Portuguese"
    assert message_joao["original_text"] == "Hello"
    assert message_joao["translations"] == {}
    assert len(message_joao["message_id"].strip())
    assert len(message_joao["sent_at"].strip())

    assert message_maria["type"] == "private_message"
    assert message_maria["sender_nickname"] == "joao"
    assert message_maria["recipient_nickname"] == "maria"
    assert message_maria["sender_language"] == "Portuguese"
    assert message_maria["original_text"] == "Hello"
    assert message_maria["translations"] == {}
    assert len(message_maria["message_id"].strip())
    assert len(message_maria["sent_at"].strip())
