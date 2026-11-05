from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ItemCreate(BaseModel):
    title: str
    description: Optional[str] = None
    price: float

class ItemResponse(ItemCreate):
    id: int
    owner_id: int

    class Config:
        from_attributes = True
