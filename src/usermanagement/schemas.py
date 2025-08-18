from pydantic import BaseModel
from uuid import UUID

class UserManagementBase(BaseModel):

    id_role: str
    email: str
    account_type: str

class UserManagementCreate(UserManagementBase):
    pass

class UserManagementUpdate(BaseModel):
    id_user: str | None = None  # Add this line
    id_role: str | None = None
    account_type: str | None = None

class UserManagementOut(UserManagementBase):
    id: UUID
    id_user: str | None = None
    role_name: str | None = None


class userCheckemail(BaseModel):
    email:str
    id_user: str | None = None

class RoleOut(BaseModel):
    id: UUID
    name: str

class RoleName(BaseModel):
    name: str