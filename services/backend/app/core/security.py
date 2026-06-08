from datetime import UTC, datetime, timedelta

import jwt
from jwt import InvalidTokenError as PyJWTInvalidTokenError

from app.core.config import get_settings
from app.schemas.auth import TokenPayload


class InvalidTokenError(Exception):
    """Raised when a token is missing, malformed, expired, or has a bad signature."""


def encode_jwt(*, nickname: str, language: str, expires_in_minutes: int | None = None) -> str:
    settings = get_settings()
    minutes = expires_in_minutes if expires_in_minutes is not None else settings.jwt_expires_minutes
    now = datetime.now(UTC)
    payload = {
        "nickname": nickname,
        "language": language,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_jwt(token: str) -> TokenPayload:
    settings = get_settings()
    try:
        raw = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except PyJWTInvalidTokenError as exc:
        raise InvalidTokenError(str(exc)) from exc
    return TokenPayload(**raw)
