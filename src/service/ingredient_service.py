from fastapi import Request

from database.orm import Ingredient
from exception.ingredient_exception import IngredientNotFoundException
from schema.request import IngredientRequest
from schema.response import IngredientListSchema, IngredientSchema, IngredientNameListResponse


class IngredientService:
    def __init__(self, user_repo, ingredient_repo, user_service, access_token: str, req: Request):
        self.user_repo = user_repo
        self.ingredient_repo = ingredient_repo
        self.user_service = user_service
        self.access_token = access_token
        self.req = req

    async def get_current_user(self):
        return await self.user_service.get_user_by_token(self.access_token, self.req)

    async def create_ingredient(self, request: IngredientRequest) -> IngredientSchema:
        current_user = await self.get_current_user()

        ingredient = Ingredient(
            user_id=current_user.id,
            ingredient_name=request.ingredient_name,
            category_id=request.category_id,
            purchase_date=request.purchase_date
        )
        await self.ingredient_repo.create_ingredient(ingredient)

        return IngredientSchema.model_validate(ingredient)

    async def get_detail_ingredients(self):
        user = await self.get_current_user()
        ingredients = await self.ingredient_repo.get_ingredients(user.id)

        return IngredientListSchema(ingredients=ingredients)

    async def get_ingredients(self):
        user = await self.get_current_user()
        ingredients = await self.ingredient_repo.get_ingredients(user.id)

        ingredient_names = [ingredient.ingredient_name for ingredient in ingredients]

        return IngredientNameListResponse(ingredient_list=ingredient_names)

    async def delete_ingredient(self, ingredient_id: int):
        user = await self.get_current_user()
        success = await self.ingredient_repo.delete_ingredient(user.id, ingredient_id)

        if not success:
            raise IngredientNotFoundException()