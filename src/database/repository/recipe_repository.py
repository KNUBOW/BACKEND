import json
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, update

from database.orm import LikeRecipe
from database.repository.base_repository import commit_with_error_handling
from sqlalchemy import func
from database.orm import FoodRanking


class RecipeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_recipe_data(self, user_id: int, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        clean_recipe_data = {k: v for k, v in recipe_data.items() if k != "_ai_provider"}   # _ai_provider 값 삭제

        recipe_json = json.dumps(clean_recipe_data, ensure_ascii=False)

        like_recipe = LikeRecipe(
            user_id=user_id,
            recipe=recipe_json,
            status=True
        )

        self.session.add(like_recipe)
        await commit_with_error_handling(self.session, context="레시피 저장")
        await self.session.refresh(like_recipe)

        return {
            "id": like_recipe.id,
            "recipe": json.loads(like_recipe.recipe),
            "status": like_recipe.status,
        }

    async def get_recipes_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        stmt = select(LikeRecipe).where(
            and_(
                LikeRecipe.user_id == user_id,
                LikeRecipe.status == True
            )
        ).order_by(LikeRecipe.created_at.desc())

        result = await self.session.execute(stmt)
        recipes = result.scalars().all()

        return [
            {
                "id": recipe.id,
                "recipe": json.loads(recipe.recipe),
            }
            for recipe in recipes
        ]

    async def soft_delete_recipe(self, user_id: int, recipe_id: int) -> bool:
        stmt = update(LikeRecipe).where(
            and_(
                LikeRecipe.id == recipe_id,
                LikeRecipe.user_id == user_id,
                LikeRecipe.status == True
            )
        ).values(status=False)

        result = await self.session.execute(stmt)
        await commit_with_error_handling(self.session, context="레시피 삭제")

        return result.rowcount > 0

    async def log_food_ranking(self, food_name: str) -> None:   # food_ranking 로그 수집
        if not food_name:
            return
        entry = FoodRanking(food_name=food_name)
        self.session.add(entry)
        await commit_with_error_handling(self.session, context="음식 랭킹 기록")

    async def get_food_ranking(self, limit: int = 20) -> List[Dict[str, Any]]:  # ranking 조회
        stmt = (
            select(
                FoodRanking.food_name,
                func.count(FoodRanking.id).label("count")
            )
            .group_by(FoodRanking.food_name)
            .order_by(func.count(FoodRanking.id).desc(), FoodRanking.food_name.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [
            {"food_name": row.food_name, "count": row.count}
            for row in rows
        ]