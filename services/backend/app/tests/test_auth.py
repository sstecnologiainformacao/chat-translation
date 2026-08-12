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

    client.post(
        "/auth/register",
        json={
            "username": "test-user@deploy.co",
            "password": "test-pass",
            "language": "Portugues",
            "nickname": "Joao",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "username": "test-user@deploy.co",
            "password": "test-pass",
        },
    )

    assert response.status_code == 200
    token = response.json()["token"]
    payload = decode_jwt(token)
    assert payload.nickname == "Joao"
    assert payload.language == "Portugues"


def test_register_user_success_returns_created_user(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={
            "username": "joao@deploy.co",
            "password": "local-pass",
            "language": "Portugues",
            "nickname": "Joao",
        },
    )

    assert response.status_code == 201
    assert response.json() == {"username": "joao@deploy.co"}


def test_register_user_rejects_non_deploy_email(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={
            "username": "joao@example.com",
            "password": "local-pass",
            "nickname": "Joao",
            "language": "Portugues",
        },
    )

    assert response.status_code == 422


def test_register_user_rejects_duplicate_username(client: TestClient) -> None:
    payload = {
        "username": "joao@deploy.co",
        "password": "local-pass",
        "nickname": "Joao",
        "language": "Portugues",
    }

    first_response = client.post("/auth/register", json=payload)
    second_response = client.post("/auth/register", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "user_already_exists"


def test_login_success_with_registered_user(client: TestClient) -> None:
    from app.core.security import decode_jwt

    register_response = client.post(
        "/auth/register",
        json={
            "username": "maria@deploy.co",
            "password": "local-pass",
            "nickname": "maria",
            "language": "English",
        },
    )
    login_response = client.post(
        "/auth/login",
        json={
            "username": "maria@deploy.co",
            "password": "local-pass",
        },
    )

    assert register_response.status_code == 201
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    payload = decode_jwt(token)
    assert payload.nickname == "maria"
    assert payload.language == "English"


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
