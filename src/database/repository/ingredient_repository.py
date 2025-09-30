from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, and_

from database.orm import Ingredient
from database.repository.base_repository import commit_with_error_handling


class IngredientRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_ingredient(self, ingredient: Ingredient) -> Ingredient:
        self.session.add(ingredient)
        await commit_with_error_handling(self.session)
        await self.session.refresh(ingredient)
        return ingredient

    async def get_ingredients(self, user_id: int):
        stmt = select(Ingredient).where(Ingredient.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_ingredients_by_user(self, user):
        return await self.get_ingredients(user.id)

    async def get_ingredient_by_id(self, user_id: int, ingredient_id: int) -> Ingredient | None:
        stmt = select(Ingredient).where(
            and_(Ingredient.user_id == user_id, Ingredient.id == ingredient_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_ingredient(self, user_id: int, ingredient_id: str) -> bool:
        stmt = delete(Ingredient).where(
            and_(Ingredient.user_id == user_id, Ingredient.id == ingredient_id)
        )
        result = await self.session.execute(stmt)
        await commit_with_error_handling(self.session, context="식재료 삭제")
        return result.rowcount > 0