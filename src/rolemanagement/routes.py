from fastapi import APIRouter, Depends, status
from .handler import RoleHandler
from .schemas import RoleCreate, RoleUpdate, RoleOut, RoleUserCountOut, StatusResponse
from typing import List
from uuid import UUID
# Ganti dengan dependency superadmin Anda
from ..utils.dependecies import get_current_superadmin 

router = APIRouter(
    tags=["Role Management"],
    dependencies=[Depends(get_current_superadmin)] # Lindungi semua endpoint ini
)
handler = RoleHandler()

@router.get("/", response_model=List[RoleOut])
def list_roles():
    return handler.get_all_roles()

@router.post("/", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
def create_role(role_data: RoleCreate):
    return handler.create_role(role_data)

@router.put("/{role_id}", response_model=RoleOut)
def update_role(role_id: UUID, role_data: RoleUpdate):
    return handler.update_role(role_id, role_data)

@router.delete("/{role_id}", response_model=StatusResponse)
def delete_role(role_id: UUID):
    handler.delete_role(role_id)
    return {"status": "success", "message": "Role deleted successfully"}

@router.get("/{role_id}/user-count", response_model=RoleUserCountOut)
def get_user_count_for_role(role_id: UUID):
    return handler.get_role_user_details(role_id)