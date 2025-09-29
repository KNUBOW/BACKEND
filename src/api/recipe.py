from fastapi import APIRouter, Depends

from core.di import get_foodthing_service
from schema.request import FoodCookRequest, IngredientCookRequest, FoodOnlyRequest
from service.recipe_service import FoodThingAIService

router = APIRouter(prefix="/recipe", tags=["Recipe"])

@router.get("/suggest", status_code=200)
async def suggest_recipe(
    foodthing: FoodThingAIService = Depends(get_foodthing_service)
):
    return await foodthing.get_suggest_recipes()

@router.post("/cook", status_code=200)
async def cook_recipe(
    request: FoodCookRequest,
    foodthing: FoodThingAIService = Depends(get_foodthing_service)
):
    return await foodthing.get_food_recipe(request.dict())

@router.post("/ingredient-cook", status_code=200)    #식재료만 ->
async def ingredient_recipe(
    request: IngredientCookRequest,
    foodthing: FoodThingAIService = Depends(get_foodthing_service)
):
    return await foodthing.get_quick_recipe(request.chat)

@router.post("/food-cook", status_code=200)    #음식명만 ex-> 계란후라이
async def food_recipe(
    request: FoodOnlyRequest,
    foodthing: FoodThingAIService = Depends(get_foodthing_service)
):
    return await foodthing.get_search_recipe(request.chat)
