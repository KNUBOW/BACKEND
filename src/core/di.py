from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import TypeVar, Type
from functools import partial

from core.connection import get_postgres_db
from database.repository.board_repository import BoardRepository
from database.repository.ingredient_repository import IngredientRepository

from database.repository.user_repository import UserRepository
from service.auth.google_auth_service import GoogleAuthService
from service.auth.jwt_handler import get_access_token
from service.auth.kakao_auth_service import KakaoAuthService
from service.auth.naver_auth_service import NaverAuthService
from service.board_service import BoardService
from service.ingredient_service import IngredientService
from service.recipe_service import FoodThingAIService
from service.user_service import UserService


# ------------------- 리포지토리 관련 DI -------------------
def get_user_repo(session: AsyncSession = Depends(get_postgres_db)) -> UserRepository:
    return UserRepository(session)

def get_ingredient_repo(session: AsyncSession = Depends(get_postgres_db)) -> IngredientRepository:
    return IngredientRepository(session)

def get_board_repo(session: AsyncSession = Depends(get_postgres_db)) -> BoardRepository:
    return BoardRepository(session)

# ------------------- 서비스 관련 DI -------------------
def get_user_service(user_repo: UserRepository = Depends(get_user_repo)) -> UserService:
    return UserService(user_repo)

def get_ingredient_service(
    req: Request,
    ingredient_repo: IngredientRepository = Depends(get_ingredient_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    user_service: UserService = Depends(get_user_service),
    access_token: str = Depends(get_access_token),
) -> IngredientService:
    return IngredientService(
        user_repo=user_repo,
        ingredient_repo=ingredient_repo,
        user_service=user_service,
        access_token=access_token,
        req=req
    )

def get_board_service(
    req: Request,
    user_repo: UserRepository = Depends(get_user_repo),
    board_repo: BoardRepository = Depends(get_board_repo),
    user_service: UserService = Depends(get_user_service),
    access_token: str = Depends(get_access_token),
) -> BoardService:
    return BoardService(
        user_repo=user_repo,
        board_repo=board_repo,
        user_service=user_service,
        access_token=access_token,
        req=req
    )

def get_foodthing_service(
    request: Request,
    user_service: UserService = Depends(get_user_service),
    user_repo: UserRepository = Depends(get_user_repo),
    access_token: str = Depends(get_access_token),
) -> FoodThingAIService:
    return FoodThingAIService(
        user_service=user_service,
        user_repo=user_repo,
        access_token=access_token,
        req=request
    )


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