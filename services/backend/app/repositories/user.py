from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import UserModel
from app.repositories.base import StoredUser


class SqlAlchemyUserRepository:
    def __init__(self, *, session: AsyncSession) -> None:
        self.session = session

    async def create_user(
        self,
        *,
        username: str,
        password_hash: str,
        nickname: str,
        language: str,
    ) -> bool:
        exist_user = await self.get_user(username=username)

        if exist_user is not None:
            return False

        user = UserModel(
            username=username.lower(),
            password_hash=password_hash,
            nickname=nickname,
            language=language,
        )

        self.session.add(user)

        await self.session.commit()
        await self.session.refresh(user)

        return True

    async def get_user(self, *, username: str) -> StoredUser | None:
        statement = select(UserModel).where(UserModel.username == username.lower())

        result = await self.session.execute(statement)
        user_model: UserModel | None = result.scalar_one_or_none()
        if user_model is None:
            return None

        return StoredUser(
            username=user_model.username,
            password_hash=user_model.password_hash,
            language=user_model.language,
            nickname=user_model.nickname,
        )
