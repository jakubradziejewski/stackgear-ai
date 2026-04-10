from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserCreate(BaseModel):
    """What admin sends when creating a new account."""
    email: EmailStr
    username: str
    password: str
    is_admin: bool = False


class UserRead(BaseModel):
    """What the API returns when reading a user."""
    id: str
    email: EmailStr
    username: str
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    """What a user sends to log in."""
    email: EmailStr
    password: str