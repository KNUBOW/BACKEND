from pydantic import BaseModel, EmailStr, constr, field_validator, Field
from datetime import date
from typing import Literal, Optional, List

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
    password: str