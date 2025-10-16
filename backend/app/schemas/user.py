from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    email:EmailStr
    username:str=Field(..., min_length=3, max_length=50)
    full_name:Optional[str]=None

class UserCreate(UserBase):
    password:str=Field(..., min_length=6, max_length=100)
    initial_capital:Optional[float]=Field(default=10000.0, gt=0)
    risk_tolerance:Optional[str]=Field(default="medium")

class UserUpdate(BaseModel):
    full_name:Optional[str]=None
    initial_capital:Optional[float]=None
    risk_tolerance:Optional[str]=None

class UserResponse(UserBase):
    id:int
    is_active:bool
    is_verified:bool
    created_at:datetime
    initial_capital:float
    risk_tolerance:str

    model_config=ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    username:str
    password:str

class Token(BaseModel):
    access_token:str
    token_type:str="bearer" 

class TokenData(BaseModel):
    user_id:Optional[int]=None
    username:Optional[str]=None

