from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID

# Skema untuk menampilkan data permission
class PermissionOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

# Skema dasar untuk Role
class RoleBase(BaseModel):
    name: str = Field(..., max_length=50)
    description: Optional[str] = None

class RoleCreate(RoleBase):
    id_team: UUID
    permission_ids: Optional[List[int]] = None

class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    description: Optional[str] = None
    # Field untuk permission_ids, juga opsional
    permission_ids: Optional[List[int]] = None

# Skema output untuk Role, termasuk daftar permission-nya
class RoleOut(RoleBase):
    id: UUID
    id_team: Optional[UUID] = None
    permissions: List[PermissionOut] = []

    class Config:
        from_attributes = True

# Skema generik untuk pesan status
class StatusResponse(BaseModel):
    status: str
    message: str

class RolePermissionUpdate(BaseModel):
    """
    Skema untuk menerima daftar ID permission di request body.
    """
    permission_ids: List[int] = Field(..., description="Daftar ID permission yang akan ditetapkan ke role.")

