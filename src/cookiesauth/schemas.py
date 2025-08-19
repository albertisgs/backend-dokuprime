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
    id: UUID
    username: str
    email: str 
    # --- CHANGE HERE ---
    id_team: UUID
    id_role: str | None = None 
    team_name:str
    account_type: str
    photo_url: str | None = None
    access_list: List[str] = []
    permissions: List[str] = []

    
    class Config:
        orm_mode = True # from_attributes = True for Pydantic v2

class StatusResponse(BaseModel):
    """A generic response model for status messages."""
    status: str
    message: str