import pytest
from fastapi.testclient import TestClient


def test_encode_then_decode_returns_payload() -> None:
    from app.core.security import decode_jwt, encode_jwt

    token = encode_jwt(nickname="joao", language="Portuguese", expires_in_minutes=10)
    payload = decode_jwt(token)
    assert payload.nickname == "joao"
    assert payload.language == "Portuguese"


def test_decode_rejects_expired_token() -> None:
    from app.core.security import InvalidTokenError, decode_jwt, encode_jwt

    token = encode_jwt(nickname="joao", language="Portuguese", expires_in_minutes=-1)
    with pytest.raises(InvalidTokenError):
        decode_jwt(token)


def test_decode_rejects_tampered_signature() -> None:
    from app.core.security import InvalidTokenError, decode_jwt, encode_jwt

    token = encode_jwt(nickname="joao", language="Portuguese", expires_in_minutes=10)
    tampered = token[:-3] + ("aaa" if token[:-3] != "aaa" else "bbb")
    with pytest.raises(InvalidTokenError):
        decode_jwt(tampered)


def test_login_success_returns_token(client: TestClient) -> None:
    from app.core.security import decode_jwt

    response = client.post(
        "/auth/login",
        json={
            "username": "test-user",
            "password": "test-pass",
            "nickname": "joao",
            "language": "Portuguese",
        },
    )

    assert response.status_code == 200
    token = response.json()["token"]
    payload = decode_jwt(token)
    assert payload.nickname == "joao"
    assert payload.language == "Portuguese"


def test_login_wrong_password_returns_401(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        json={
            "username": "test-user",
            "password": "wrong-pass",
            "nickname": "joao",
            "language": "Portuguese",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"


def test_login_wrong_username_returns_401(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        json={
            "username": "wrong-user",
            "password": "test-pass",
            "nickname": "joao",
            "language": "Portuguese",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"


def test_login_missing_field_returns_422(client: TestClient) -> None:
    response = client.post("/auth/login", json={"username": "test-user"})

    assert response.status_code == 422
