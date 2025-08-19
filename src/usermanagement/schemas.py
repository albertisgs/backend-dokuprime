# src/usermanagement/schemas.py (Updated)

from pydantic import BaseModel
from uuid import UUID

class UserManagementBase(BaseModel):
    # --- CHANGE HERE ---
    id_team: str
    id_role: str | None = None  
    email: str
    account_type: str

class UserManagementCreate(UserManagementBase):
    pass

class UserManagementUpdate(BaseModel):
    id_user: str | None = None
    # --- CHANGE HERE ---
    id_team: str | None = None
    id_role: str | None = None  
    account_type: str | None = None

class UserManagementOut(UserManagementBase):
    id: UUID
    id_user: str | None = None
    # --- CHANGE HERE ---
    team_name: str | None = None
    id_role: str | None = None  

class userCheckemail(BaseModel):
    email:str
    id_user: str | None = None

# --- CHANGE HERE ---
class TeamOut(BaseModel):
    id: UUID
    name: str

class TeamName(BaseModel):
    name: str