# Import Request from fastapi
from fastapi import Depends, HTTPException, status, Request
from .sessionrepository import SessionRepository 
from .sessiondependencies import get_current_user_profile

SUPERADMIN_ROLE_ID = "8ea384d2-9d47-49d7-be95-b45d08a07aa3"

async def get_current_superadmin(request: Request): # Inject the full Request
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


    # Check for superadmin role from session_data
    if str(user_mngmnt_data.get("id_role")) != SUPERADMIN_ROLE_ID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: Requires superadmin role.",
        )

    # You can return the session data or fetch the full user object
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
