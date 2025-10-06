from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import TypeVar, Type, Callable

from database.repository.recipe_repository import RecipeRepository
from src.core.connection import get_postgres_db
from src.database.repository.board_repository import BoardRepository
from src.database.repository.ingredient_repository import IngredientRepository

from src.database.repository.user_repository import UserRepository
from src.service.auth.google_auth_service import GoogleAuthService
from src.service.auth.jwt_handler import get_access_token
from src.service.auth.kakao_auth_service import KakaoAuthService
from src.service.auth.naver_auth_service import NaverAuthService
from src.service.board_service import BoardService
from src.service.ingredient_service import IngredientService
from src.service.recipe_service import FoodThingAIService, RecipeManagementService
from src.service.user_service import UserService


# ------------------- 리포지토리 관련 DI -------------------
def get_user_repo(session: AsyncSession = Depends(get_postgres_db)) -> UserRepository:
    return UserRepository(session)

def get_ingredient_repo(session: AsyncSession = Depends(get_postgres_db)) -> IngredientRepository:
    return IngredientRepository(session)

def get_board_repo(session: AsyncSession = Depends(get_postgres_db)) -> BoardRepository:
    return BoardRepository(session)

def get_recipe_repository(session: AsyncSession = Depends(get_postgres_db)) -> RecipeRepository:
    return RecipeRepository(session)

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
    recipe_repo: RecipeRepository = Depends(get_recipe_repository),
) -> FoodThingAIService:
    return FoodThingAIService(
        user_service=user_service,
        user_repo=user_repo,
        access_token=access_token,
        req=request,
        recipe_repo=recipe_repo
    )

def get_recipe_management_service(
    request: Request,
    recipe_repo: RecipeRepository = Depends(get_recipe_repository),
    user_service: UserService = Depends(get_user_service),
    access_token: str = Depends(get_access_token),
) -> RecipeManagementService:
    return RecipeManagementService(
        recipe_repo=recipe_repo,
        user_service=user_service,
        access_token=access_token,
        req=request
    )


# ------------------- AuthService 팩토리 패턴 -------------------
T = TypeVar("T")

def create_auth_service_dependency(
    service_class: Type[T],
) -> Callable[[UserService, UserRepository], T]:
    def dependency(
        user_service: UserService = Depends(get_user_service),
        user_repo: UserRepository = Depends(get_user_repo),
    ) -> T:
        return service_class(user_service, user_repo)

    return dependency

# ------------------- 소셜별 AuthService -------------------
get_google_auth_service = create_auth_service_dependency(GoogleAuthService)
get_naver_auth_service = create_auth_service_dependency(NaverAuthService)
get_kakao_auth_service = create_auth_service_dependency(KakaoAuthService)

