from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID

# Daftar hak akses yang valid di aplikasi Anda
VALID_ACCESS_RIGHTS = [
    "dashboard","knowledge-base","market-competitor-insight","prompt-management","upload-document","sipp-case-details","user-management","role-management"
]

class RoleBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    access: List[str] = Field(default=[], description="List of access rights")

class RoleCreate(RoleBase):
    pass

class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=50)
    access: Optional[List[str]] = None

class RoleOut(RoleBase):
    id: UUID

    class Config:
        from_attributes = True


# Skema baru untuk respon jumlah pengguna
class RoleUserCountOut(BaseModel):
    role_id: UUID
    user_count: int
    usernames: List[str]
    
# Skema generik untuk pesan status
class StatusResponse(BaseModel):
    status: str
    message: str