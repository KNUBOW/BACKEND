from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import date

class UserSchema(BaseModel):
    id: int
    email: EmailStr
    name: str
    nickname: str

    model_config = {"from_attributes": True}

class JWTResponse(BaseModel):
    access_token:str

class FindIdResponse(BaseModel):
    email: str

class IngredientSchema(BaseModel):
    id: int
    user_id: int
    ingredient_name: str
    category_id: int
    purchase_date: date

    model_config = {"from_attributes": True}

class IngredientListSchema(BaseModel):
    ingredients: List[IngredientSchema]