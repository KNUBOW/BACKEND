from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import TypeVar, Type
from functools import partial

from core.connection import get_postgres_db

from database.repository.user_repository import UserRepository
from service.auth.google_auth_service import GoogleAuthService
from service.auth.kakao_auth_service import KakaoAuthService
from service.auth.naver_auth_service import NaverAuthService
from service.user_service import UserService


# ------------------- 리포지토리 관련 DI -------------------
def get_user_repo(session: AsyncSession = Depends(get_postgres_db)) -> UserRepository:
    return UserRepository(session)

# ------------------- 서비스 관련 DI -------------------
def get_user_service(user_repo: UserRepository = Depends(get_user_repo)) -> UserService:
    return UserService(user_repo)

# ------------------- AuthService 공통 팩토리 -------------------
T = TypeVar("T")
def get_auth_service(
    service_class: Type[T],
    user_service: UserService = Depends(get_user_service),
    user_repo: UserRepository = Depends(get_user_repo),
) -> T:
    return service_class(user_service, user_repo)

# ------------------- 소셜별 AuthService -------------------
get_google_auth_service = partial(get_auth_service, GoogleAuthService)
get_naver_auth_service = partial(get_auth_service, NaverAuthService)
get_kakao_auth_service = partial(get_auth_service, KakaoAuthService)