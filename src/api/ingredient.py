from fastapi import APIRouter, Depends, Path

from core.di import get_ingredient_service
from schema.request import IngredientRequest
from schema.response import IngredientSchema, IngredientNameListResponse, IngredientListSchema
from service.ingredient_service import IngredientService

router = APIRouter(prefix="/ingredients", tags=["ingredients"])

@router.post("", status_code=201, response_model=IngredientSchema)
async def create_ingredient(
    request: IngredientRequest,
    service: IngredientService = Depends(get_ingredient_service)
):
    return await service.create_ingredient(request)

@router.get("", status_code=200, response_model=IngredientNameListResponse)
async def get_ingredients(
    service: IngredientService = Depends(get_ingredient_service)
):
    return await service.get_ingredients()

@router.get("/detail", status_code=200, response_model=IngredientListSchema)
async def get_detail_ingredients(
    service: IngredientService = Depends(get_ingredient_service)
):
    return await service.get_detail_ingredients()

@router.get("/{ingredient_id}", status_code=200, response_model=IngredientSchema)
async def get_ingredient_by_id(
    ingredient_id: int = Path(..., title="식재료 ID", ge=1),
    service: IngredientService = Depends(get_ingredient_service)
):
    return await service.get_ingredient_by_id(ingredient_id)

@router.delete("", status_code=204)
async def delete_ingredient(
    ingredient_id: int,
    service: IngredientService = Depends(get_ingredient_service)
):
    await service.delete_ingredient(ingredient_id)