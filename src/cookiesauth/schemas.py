from pydantic import BaseModel 
from uuid import UUID
from typing import List

class UserCreate(BaseModel):
    username: str
    email: str 
    password: str

class UserLogin(BaseModel):
    email: str 
    password: str

class UserOut(BaseModel):
    """Defines the public-facing user model."""
    id: UUID
    username: str
    email: str 
    id_role: UUID
    role_name:str
    account_type: str
    photo_url: str | None = None
    access_list: List[str] = []
    

    class Config:
        orm_mode = True

class StatusResponse(BaseModel):
    """A generic response model for status messages."""
    status: str
    message: str