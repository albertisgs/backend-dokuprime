# src/utils/dependecies.py (Updated)

from fastapi import Depends, HTTPException, status, Request
from .sessionrepository import SessionRepository 
from .sessiondependencies import get_current_user_profile

# --- TIDAK BERUBAH ---
SUPERADMIN_TEAM_ID = "8ea384d2-9d47-49d7-be95-b45d08a07aa3" # Renamed variable for clarity

async def get_current_superadmin(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session_repo = SessionRepository()
    session_data = session_repo.get_session_data(session_id)

    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user_mngmnt_data = session_repo.get_by_user_id(session_data.get("user_id"))

    if not user_mngmnt_data:
        raise HTTPException(status_code=401, detail="your're not allowed")

    if str(user_mngmnt_data.get("id_team")) != SUPERADMIN_TEAM_ID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: Requires superadmin team.",
        )

    return session_data

# --- TIDAK BERUBAH ---
def require_access(required_right: str):
    def dependency(user: dict = Depends(get_current_user_profile)) -> dict:
        # Superadmin always has access
        if str(user.get("id_team")) == SUPERADMIN_TEAM_ID:
            return user
        
        if required_right not in user.get("access_list", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Requires '{required_right}' access."
            )
        return user
    return dependency

# --- PERUBAHAN UTAMA ---
# Fungsi ini sekarang menjadi dependency utama untuk manajemen terdelegasi
def require_permission(required_permission: str):
    """
    Dependency yang memeriksa izin pengguna dengan logika baru:
    1. Jika pengguna adalah superadmin, selalu berikan akses.
    2. Jika bukan, periksa apakah pengguna memiliki izin spesifik yang diperlukan.
    3. Jika memiliki izin, kembalikan profil pengguna (yang berisi id_team).
    4. Jika tidak, tolak akses.
    """
    def dependency(user: dict = Depends(get_current_user_profile)) -> dict:
        # 1. Superadmin selalu memiliki akses penuh dan dapat melihat semua data
        if str(user.get("id_team")) == SUPERADMIN_TEAM_ID:
            return user

        # 2. Periksa izin spesifik untuk pengguna non-superadmin
        if required_permission not in user.get("permissions", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Requires '{required_permission}' permission."
            )
        
        # 3. Pengguna memiliki izin, kembalikan profil mereka untuk filtering di level data
        return user
    return dependency
