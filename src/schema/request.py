from pydantic import BaseModel, EmailStr, constr
from datetime import date
from typing import Literal, List

class SignUpRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=8, max_length=20)
    checked_password: constr(min_length=8, max_length=20)
    name: constr(min_length=2, max_length=20)
    nickname: constr(min_length=2, max_length=20)
    birth: date
    gender: Literal["male", "female"]
    phone_num: constr(min_length=10, max_length=11)

class LogInRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=8, max_length=20)

class PassWordChangeRequest(BaseModel):
    current_password: constr(min_length=8, max_length=20)
    new_password: constr(min_length=8, max_length=20)
    confirm_password: constr(min_length=8, max_length=20)

class FindIdRequest(BaseModel):
    name: constr(min_length=2, max_length=20)
    birth: date
    phone_num: constr(min_length=10, max_length=11)

class IngredientRequest(BaseModel):
    ingredient_name: constr(min_length=1, max_length=40)
    category_id: int
    purchase_date: date

class FoodCookRequest(BaseModel):
    food: str
    use_ingredients: List[str] = []

class IngredientCookRequest(BaseModel):
    chat: str

class FoodOnlyRequest(BaseModel):
    chat: str
