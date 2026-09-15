from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_database_session
from app.repositories.base import UserRepository
from app.repositories.user import SqlAlchemyUserRepository
from app.services.auth import AuthService


async def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> AsyncGenerator[SqlAlchemyUserRepository, None]:
    user_repository: SqlAlchemyUserRepository = SqlAlchemyUserRepository(session=session)
    yield user_repository


async def get_auth_service(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> AsyncGenerator[AuthService, None]:
    auth_service: AuthService = AuthService(user_repository=user_repository)
    yield auth_service
