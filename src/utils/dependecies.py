# src/utils/dependecies.py (Updated)

from fastapi import Depends, HTTPException, status, Request
from .sessionrepository import SessionRepository 
from .sessiondependencies import get_current_user_profile

# --- CHANGE HERE ---
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

    # --- CHANGE HERE ---
    # Check for superadmin team from user_mngmnt_data
    if str(user_mngmnt_data.get("id_team")) != SUPERADMIN_TEAM_ID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: Requires superadmin team.",
        )

    return session_data

def require_access(required_right: str):
    def dependency(user: dict = Depends(get_current_user_profile)) -> dict:
        if required_right not in user.get("access_list", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Requires '{required_right}' access."
            )
        return user
    return dependency


def require_permission(required_permission: str):
    """
    Memastikan user memiliki permission spesifik (misal: 'document:edit').
    Dependency ini akan melakukan dua level pengecekan:
    1. Apakah tim user memiliki akses ke modul utama?
    2. Apakah role user memiliki permission spesifik yang diminta?
    """
    def dependency(user: dict = Depends(get_current_user_profile)) -> dict:
        # 1. Cek akses modul di level tim
        # contoh: 'document' dari 'document:edit'
        module = required_permission.split(':')[0] 
        if module not in user.get("team_modules", []):
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Your team does not have access to the '{module}' module."
            )

        # 2. Cek permission spesifik di level role
        if required_permission not in user.get("permissions", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Requires '{required_permission}' permission."
            )
        return user
    return dependency