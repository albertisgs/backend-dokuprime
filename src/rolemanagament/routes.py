from fastapi import APIRouter, Depends, status
from typing import List
from uuid import UUID
from .handler import RoleHandler
from .schemas import RoleCreate, RoleOut, PermissionOut, StatusResponse, RolePermissionUpdate
from ..utils.dependecies import get_current_superadmin

router = APIRouter(
    tags=["Role Management"],
    dependencies=[Depends(get_current_superadmin)] # Hanya Superadmin yang bisa akses
)
handler = RoleHandler()

@router.get("/", response_model=List[RoleOut])
def list_roles():
    """Mendapatkan daftar semua role beserta permission-nya."""
    return handler.get_all_roles()

@router.post("/", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
def create_role(role_data: RoleCreate):
    """Membuat role baru."""
    return handler.create_role(role_data)

@router.post("/{role_id}/permissions/{permission_id}", response_model=StatusResponse)
def add_permission_to_role(role_id: UUID, permission_id: int):
    """Menambahkan permission ke sebuah role."""
    return handler.add_permission(role_id, permission_id)

@router.delete("/{role_id}/permissions/{permission_id}", response_model=StatusResponse)
def remove_permission_from_role(role_id: UUID, permission_id: int):
    """Menghapus permission dari sebuah role."""
    return handler.remove_permission(role_id, permission_id)

@router.get("/permissions/all", response_model=List[PermissionOut])
def list_all_available_permissions():
    """Mendapatkan daftar semua permission yang ada di sistem."""
    return handler.get_all_permissions()

@router.put("/{role_id}/permissions", response_model=StatusResponse)
def set_permissions_for_role(role_id: UUID, data: RolePermissionUpdate):
    """
    Mengatur/mengganti semua permission untuk sebuah role.
    Kirim daftar ID permission di dalam request body.
    Contoh: { "permission_ids": [1, 2, 5] }
    """
    return handler.set_permissions(role_id, data.permission_ids)
