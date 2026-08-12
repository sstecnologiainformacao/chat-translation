from fastapi import APIRouter, HTTPException, Request, status

from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse
from app.services.auth import AuthService, InvalidCredentialsError, UserAlreadyExistsError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, request: Request) -> LoginResponse:
    auth_service: AuthService = request.app.state.auth_service

    try:
        token = await auth_service.login(
            username=payload.username,
            password=payload.password,
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_credentials",
        ) from None

    return LoginResponse(token=token)


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, request: Request) -> RegisterResponse:
    auth_service: AuthService = request.app.state.auth_service

    try:
        username = await auth_service.register(
            username=str(payload.username),
            password=payload.password,
            nickname=payload.nickname,
            language=payload.language,
        )
    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="user_already_exists",
        ) from None

    return RegisterResponse(username=username)
