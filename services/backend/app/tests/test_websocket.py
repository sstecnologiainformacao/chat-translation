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