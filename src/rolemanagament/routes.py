from fastapi import APIRouter, Depends, status, HTTPException
from typing import List
from uuid import UUID
from .handler import RoleHandler
from .schemas import RoleCreate, RoleOut, PermissionOut, StatusResponse, RolePermissionUpdate, RoleUpdate
from ..utils.dependecies import require_permission, get_current_superadmin, SUPERADMIN_TEAM_ID
from ..utils.sessiondependencies import get_current_user_profile

router = APIRouter(
    tags=["Role Management"],
    dependencies=[Depends(require_permission("rolemanagement:master"))]
)
superadmin_router = APIRouter(
    tags=["Role Management (Superadmin)"],
    dependencies=[Depends(get_current_superadmin)]
)
handler = RoleHandler()

@superadmin_router.get("/super_admin/all", response_model=List[RoleOut])
def list_all_roles_globally():
    return handler.get_all_roles()

@router.get("/permissions/all", response_model=List[PermissionOut])
def list_all_available_permissions():
    return handler.get_all_permissions()

@router.get("/", response_model=List[RoleOut])
def list_roles_for_team(current_user: dict = Depends(get_current_user_profile)):
    team_id = current_user.get("id_team")
    is_super_admin = str(team_id) == SUPERADMIN_TEAM_ID
    if is_super_admin:
        return handler.get_all_roles()
    return handler.get_all_roles(team_id=team_id)

@router.get("/{role_id}", response_model=RoleOut)
def get_role_details(role_id: UUID, current_user: dict = Depends(get_current_user_profile)):
    """Mendapatkan detail spesifik sebuah role, termasuk permissions-nya."""
    team_id = current_user.get("id_team")
    is_super_admin = str(team_id) == SUPERADMIN_TEAM_ID
    team_id_to_check = None if is_super_admin else team_id
    
    return handler.get_role_by_id(role_id, team_id=team_id_to_check)

@router.post("/", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
def create_role_for_team(role_data: RoleCreate, current_user: dict = Depends(get_current_user_profile)):
    admin_team_id = current_user.get("id_team")
    is_super_admin = str(admin_team_id) == SUPERADMIN_TEAM_ID
    target_team_id = role_data.id_team
    if not is_super_admin and str(target_team_id) != str(admin_team_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create roles for your own team."
        )
    return handler.create_role(role_data, team_id=target_team_id)

@router.put("/update-permissions/{role_id}", response_model=StatusResponse)
def set_permissions_for_role(role_id: UUID, data: RolePermissionUpdate, current_user: dict = Depends(get_current_user_profile)):
    team_id = current_user.get("id_team")
    is_super_admin = str(team_id) == SUPERADMIN_TEAM_ID
    team_id_to_check = None if is_super_admin else team_id
    return handler.set_permissions(role_id, data.permission_ids, team_id=team_id_to_check)

@router.delete("/{role_id}", response_model=StatusResponse)
def delete_role(role_id: UUID, current_user: dict = Depends(get_current_user_profile)):
    team_id = current_user.get("id_team")
    is_super_admin = str(team_id) == SUPERADMIN_TEAM_ID
    team_id_to_check = None if is_super_admin else team_id
    
    success = handler.delete_role(role_id, team_id=team_id_to_check)
    if not success:
        raise HTTPException(status_code=404, detail="Role not found in your team.")
    return {"status": "success", "message": "Role deleted successfully"}

@router.put("/{role_id}", response_model=StatusResponse)
def update_role_and_permissions(role_id: UUID, data: RoleUpdate, current_user: dict = Depends(get_current_user_profile)):
    """Endpoint untuk update nama, deskripsi, dan permissions role sekaligus."""
    team_id = current_user.get("id_team")
    is_super_admin = str(team_id) == SUPERADMIN_TEAM_ID
    team_id_to_check = None if is_super_admin else team_id
    return handler.update_role(role_id, data, team_id=team_id_to_check)

@router.get("/permissions/by-team/{team_id}", response_model=List[PermissionOut])
def get_available_permissions_for_team(team_id: UUID, current_user: dict = Depends(get_current_user_profile)):
    """Mengambil daftar permission yang relevan untuk sebuah tim spesifik."""
    return handler.get_filtered_permissions_for_team(team_id)
