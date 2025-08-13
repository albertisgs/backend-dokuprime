from pydantic import BaseModel 
from uuid import UUID

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
    account_type: str
    photo_url: str | None = None

    class Config:
        orm_mode = True

class StatusResponse(BaseModel):
    """A generic response model for status messages."""
    status: str
    message: str