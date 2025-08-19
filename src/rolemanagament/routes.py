from fastapi import APIRouter, Depends, status
from typing import List
from uuid import UUID
from .handler import RoleHandler
from .schemas import RoleCreate, RoleOut, PermissionOut, StatusResponse, RolePermissionUpdate
from ..utils.dependecies import require_permission, get_current_superadmin
from ..utils.sessiondependencies import get_current_user_profile


router = APIRouter(
    tags=["Role Management"],
    # Menggunakan dependency baru, contoh untuk izin master
    dependencies=[Depends(require_permission("rolemanagement:master"))] 
)

# Router terpisah HANYA untuk Superadmin (akses global)
superadmin_router = APIRouter(
    tags=["Role Management (Superadmin)"],
    dependencies=[Depends(get_current_superadmin)]
)

handler = RoleHandler()

# --- Endpoint Global (Hanya Superadmin) ---

@superadmin_router.get("/super_admin/all", response_model=List[RoleOut])
def list_all_roles_globally():
    """(Superadmin) Mendapatkan daftar SEMUA role dari semua tim."""
    return handler.get_all_roles() # Tanpa team_id

# --- Endpoint Umum ---
# Endpoint ini bisa diakses oleh siapa saja yang punya izin rolemanagement:master
@router.get("/permissions/all", response_model=List[PermissionOut])
def list_all_available_permissions():
    """Mendapatkan daftar semua permission yang ada di sistem."""
    return handler.get_all_permissions()


@router.get("/", response_model=List[RoleOut])
def list_roles_for_team(current_user: dict = Depends(get_current_user_profile)):
    """Mendapatkan daftar role HANYA untuk tim admin saat ini."""
    team_id = current_user.get("id_team")
    return handler.get_all_roles(team_id=team_id)

@router.post("/", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
def create_role_for_team(role_data: RoleCreate, current_user: dict = Depends(get_current_user_profile)):
    """Membuat role baru di dalam tim admin saat ini."""
    team_id = current_user.get("id_team")
    return handler.create_role(role_data, team_id=team_id)

@router.post("/{role_id}/permissions/{permission_id}", response_model=StatusResponse)
def add_permission_to_role(role_id: UUID, permission_id: int, current_user: dict = Depends(get_current_user_profile)):
    """Menambahkan permission ke sebuah role di dalam tim admin."""
    team_id = current_user.get("id_team")
    return handler.add_permission(role_id, permission_id, team_id)

@router.delete("/{role_id}/permissions/{permission_id}", response_model=StatusResponse)
def remove_permission_from_role(role_id: UUID, permission_id: int, current_user: dict = Depends(get_current_user_profile)):
    """Menghapus permission dari sebuah role di dalam tim admin."""
    team_id = current_user.get("id_team")
    return handler.remove_permission(role_id, permission_id, team_id)

@router.put("/{role_id}/permissions", response_model=StatusResponse)
def set_permissions_for_role(role_id: UUID, data: RolePermissionUpdate, current_user: dict = Depends(get_current_user_profile)):
    """Mengatur/mengganti semua permission untuk sebuah role di dalam tim admin."""
    team_id = current_user.get("id_team")
    return handler.set_permissions(role_id, data.permission_ids, team_id)

