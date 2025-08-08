from pydantic import BaseModel
from uuid import UUID


class RoleOut(BaseModel):
    id: UUID
    name: str
    access: list

class RoleName(BaseModel):
    name: str