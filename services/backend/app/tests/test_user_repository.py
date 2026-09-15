import uuid

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.repositories.base import StoredUser
from app.repositories.user import SqlAlchemyUserRepository


def get_async_session_maker() -> async_sessionmaker[AsyncSession]:
    settings = get_settings()

    engine = create_async_engine(
        settings.database_url,
        echo=False,
    )

    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def test_create_new_user() -> None:
    session_maker = get_async_session_maker()
    async with session_maker() as session:
        repository: SqlAlchemyUserRepository = SqlAlchemyUserRepository(session=session)

        unique_username = f"the_user_{uuid.uuid4().hex}"
        result: bool = await repository.create_user(
            username=unique_username,
            password_hash="12345678",
            nickname="the_user",
            language="Portuguese",
        )

        assert result

        user_from_db: StoredUser | None = await repository.get_user(username=unique_username)

        assert user_from_db is not None
        assert user_from_db.username == unique_username
        assert user_from_db.language == "Portuguese"
        assert user_from_db.nickname == "the_user"
        assert user_from_db.password_hash == "12345678"


async def test_get_user_returns_none_when_user_does_not_exist() -> None:
    session_maker = get_async_session_maker()
    async with session_maker() as session:
        repository: SqlAlchemyUserRepository = SqlAlchemyUserRepository(session=session)

        unique_username = f"the_user_{uuid.uuid4().hex}"

        user_from_db: StoredUser | None = await repository.get_user(username=unique_username)

        assert user_from_db is None


async def test_create_new_user_already_exists() -> None:
    session_maker = get_async_session_maker()
    async with session_maker() as session:
        repository: SqlAlchemyUserRepository = SqlAlchemyUserRepository(session=session)

        unique_username = f"the_user_{uuid.uuid4().hex}"
        result: bool = await repository.create_user(
            username=unique_username,
            password_hash="12345678",
            nickname="the_user",
            language="Portuguese",
        )

        assert result

        user_from_db: StoredUser | None = await repository.get_user(username=unique_username)

        assert user_from_db is not None
        assert user_from_db.username == unique_username
        assert user_from_db.language == "Portuguese"
        assert user_from_db.nickname == "the_user"
        assert user_from_db.password_hash == "12345678"

        new_try_same_username: bool = await repository.create_user(
            username=unique_username,
            password_hash="12345678",
            nickname="the_user",
            language="Portuguese",
        )

        assert new_try_same_username is False
