from fastapi import APIRouter, Depends

router = APIRouter(prefix="/ingredients", tags=["ingredients"])

@router.post("", status_code=201)
async def create_ingredient(
):
    pass