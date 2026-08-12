from app.core.passwords import hash_password, verify_password
from app.core.security import encode_jwt
from app.repositories.base import StoredUser, UserRepository


class InvalidCredentialsError(Exception):
    pass


class UserAlreadyExistsError(Exception):
    pass


class AuthService:
    def __init__(self, *, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    async def login(
        self,
        *,
        username: str,
        password: str,
    ) -> str:
        if not await self._credentials_match(username=username, password=password):
            raise InvalidCredentialsError
        user: StoredUser | None = await self._user_repository.get_user(username=username)
        if user is None:
            raise InvalidCredentialsError
        return encode_jwt(nickname=user.nickname, language=user.language)

    async def register(self, *, username: str, password: str, nickname: str, language: str) -> str:
        created = await self._user_repository.create_user(
            username=username,
            password_hash=hash_password(password),
            nickname=nickname,
            language=language,
        )

        if not created:
            raise UserAlreadyExistsError

        return username

    async def _credentials_match(self, *, username: str, password: str) -> bool:
        user: StoredUser | None = await self._user_repository.get_user(username=username)
        return user is not None and verify_password(
            password,
            user.password_hash,
        )
