from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.connection import get_postgres_db

from database.repository.user_repository import UserRepository
from service.user_service import UserService


# ------------------- 리포지토리 관련 DI -------------------
def get_user_repo(session: AsyncSession = Depends(get_postgres_db)) -> UserRepository:
    return UserRepository(session)

# ------------------- 서비스 관련 DI -------------------
def get_user_service(user_repo: UserRepository = Depends(get_user_repo)) -> UserService:
    return UserService(user_repo)