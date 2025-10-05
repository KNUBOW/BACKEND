from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import date, datetime

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

class IngredientNameListResponse(BaseModel):
    ingredient_list: List[str]

class BoardAuthor(BaseModel):
    user_id: int
    nickname: str

    model_config = {"from_attributes": True}


class BoardDetailResponse(BaseModel):
    id: int
    author: BoardAuthor
    title: str
    content: str
    like_count: int
    created_at: datetime
    image_urls: List[str] = []


class BoardSummaryResponse(BaseModel):
    id: int
    title: str
    author: BoardAuthor # nickname 대신 BoardAuthor 사용
    like_count: int
    exist_image: bool
    created_at: datetime