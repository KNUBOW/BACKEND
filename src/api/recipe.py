from fastapi import APIRouter, Depends

from core.di import get_foodthing_service, get_recipe_management_service
from schema.request import FoodCookRequest, IngredientCookRequest, FoodOnlyRequest, RecipeRequest
from service.recipe_service import FoodThingAIService, RecipeManagementService

router = APIRouter(prefix="/recipe", tags=["Recipe"])

"""
레시피 추출 라우터
"""
@router.get("/suggest", status_code=200)    # 식재료 기준 할 수 있는 요리 추천
async def suggest_recipe(
    foodthing: FoodThingAIService = Depends(get_foodthing_service)
):
    return await foodthing.get_suggest_recipes()

@router.post("/cook", status_code=200)  # 추천받은 걸로 레시피 알려줌
async def cook_recipe(
    request: FoodCookRequest,
    foodthing: FoodThingAIService = Depends(get_foodthing_service)
):
    return await foodthing.get_food_recipe(request.dict())

@router.post("/ingredient-cook", status_code=200)    # 식재료만 ->
async def ingredient_recipe(
    request: IngredientCookRequest,
    foodthing: FoodThingAIService = Depends(get_foodthing_service)
):
    return await foodthing.get_quick_recipe(request.chat)

@router.post("/food-cook", status_code=200)    # 음식명만 ex-> 계란후라이
async def food_recipe(
    request: FoodOnlyRequest,
    foodthing: FoodThingAIService = Depends(get_foodthing_service)
):
    return await foodthing.get_search_recipe(request.chat)

"""
레시피 저장 라우터
"""

@router.post("/like", status_code=201)  # 레시피 저장
async def save_recipe(
    request: RecipeRequest,
    recipe_service: RecipeManagementService = Depends(get_recipe_management_service)
):
    return await recipe_service.save_recipe(request.dict())

@router.get("/like", status_code=200)   # 레시피 불러오기
async def get_saved_recipe(
    recipe_service: RecipeManagementService = Depends(get_recipe_management_service)
):
    return await recipe_service.get_saved_recipes()

@router.patch("/like/{recipe_id}", status_code=204) # 저장된 레시피 삭제(소프트 삭제)
async def delete_saved_recipe(
    recipe_id: int,
    recipe_service: RecipeManagementService = Depends(get_recipe_management_service)
):
    await recipe_service.delete_recipe(recipe_id)