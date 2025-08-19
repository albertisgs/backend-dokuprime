# src/usermanagement/routes.py (Updated)

from fastapi import APIRouter, HTTPException, Depends
from .schemas import UserManagementCreate, UserManagementUpdate, UserManagementOut, userCheckemail, TeamOut, TeamName
from .handler import UserManagementHandler
from typing import List
# --- PERUBAHAN ---
from ..utils.dependecies import require_permission, get_current_superadmin
from ..utils.sessiondependencies import get_current_user_profile

# --- PERUBAHAN ---
# Router ini sekarang untuk Admin Tim (dibatasi per tim)
router = APIRouter(
    tags=["User Management"],
    dependencies=[Depends(require_permission("usermanagement:master"))]
)

# Router terpisah HANYA untuk Superadmin (akses global)
superadmin_router = APIRouter(
    tags=["User Management (Superadmin)"],
    dependencies=[Depends(get_current_superadmin)]
)

# Router publik tidak berubah
public_router = APIRouter(tags=["User Management"])
authenticated_router = APIRouter(
    tags=["User Management"],
    dependencies=[Depends(get_current_user_profile)]
)

handler = UserManagementHandler()

# --- Global Routes (Superadmin Only) ---

@superadmin_router.get("/super_admin/all", response_model=list[UserManagementOut])
def list_all_users_globally():
    """(Superadmin) Mendapatkan daftar SEMUA pengguna dari semua tim."""
    return handler.list_users() # Tanpa team_id


# --- Routes for Team Admins (Scoped to their team) ---

@router.get("/", response_model=list[UserManagementOut])
def list_users_in_team(current_user: dict = Depends(get_current_user_profile)):
    """Mendapatkan daftar pengguna HANYA dari tim admin saat ini."""
    team_id = current_user.get("id_team")
    return handler.list_users(team_id=team_id)

@router.get("/{user_management_id}", response_model=UserManagementOut)
def get_user_in_team(user_management_id: str, current_user: dict = Depends(get_current_user_profile)):
    """Mendapatkan detail pengguna HANYA jika pengguna tersebut ada di tim admin."""
    team_id = current_user.get("id_team")
    user = handler.get_user(user_management_id, team_id=team_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found in your team")
    return user

@router.post("/", response_model=UserManagementOut)
def create_user_in_team(data: UserManagementCreate, current_user: dict = Depends(get_current_user_profile)):
    """Membuat pengguna baru dan secara otomatis memasukkannya ke dalam tim admin."""
    team_id = current_user.get("id_team")
    # Pastikan data yang dikirim sesuai dengan tim admin
    if str(data.id_team) != str(team_id):
        raise HTTPException(status_code=403, detail="Cannot create user for another team.")
    return handler.create_user(data)

@router.put("/{user_management_id}", response_model=UserManagementOut)
def update_user_in_team(user_management_id: str, data: UserManagementUpdate, current_user: dict = Depends(get_current_user_profile)):
    """Memperbarui pengguna HANYA jika pengguna tersebut ada di tim admin."""
    team_id = current_user.get("id_team")
    # Admin Tim tidak boleh memindahkan user ke tim lain
    if data.id_team and str(data.id_team) != str(team_id):
         raise HTTPException(status_code=403, detail="You cannot move users to another team.")
    updated = handler.update_user(user_management_id, data, team_id=team_id)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found in your team or no data to update")
    return updated

@router.delete("/{user_management_id}")
def delete_user_in_team(user_management_id: str, current_user: dict = Depends(get_current_user_profile)):
    """Menghapus pengguna HANYA jika pengguna tersebut ada di tim admin."""
    team_id = current_user.get("id_team")
    success = handler.delete_user(user_management_id, team_id=team_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found in your team")
    return {"status": "deleted"}


# --- Public and Authenticated Routes (No Change) ---

@public_router.post("/email/check")
async def check_email(data: userCheckemail):
    return await handler.check_email_and_update(data) # Pindahkan logika ke handler

@public_router.get("/teams/", response_model=List[TeamOut])
def get_teams_list():
    return handler.list_teams()

@authenticated_router.get("/teams/{team_id}", response_model=TeamName)
def get_team_by_id(team_id: str):
    return handler.get_team(team_id)
