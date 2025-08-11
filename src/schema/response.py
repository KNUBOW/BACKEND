from pydantic import BaseModel, EmailStr

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