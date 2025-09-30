import json
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, update

from database.orm import LikeRecipe
from database.repository.base_repository import commit_with_error_handling


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