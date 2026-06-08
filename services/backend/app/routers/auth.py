from secrets import compare_digest

from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.core.security import encode_jwt
from app.schemas.auth import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest) -> LoginResponse:
    settings = get_settings()
    credentials_match = compare_digest(
        payload.username, settings.chat_user
    ) and compare_digest(payload.password, settings.chat_password)

    if not credentials_match:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_credentials",
        )

    token = encode_jwt(nickname=payload.nickname, language=payload.language)
    return LoginResponse(token=token)
