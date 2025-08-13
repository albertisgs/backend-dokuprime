from fastapi import APIRouter, HTTPException, Depends
from .schemas import UserManagementCreate, UserManagementUpdate, UserManagementOut, userCheckemail, RoleOut, RoleName
from .handler import UserManagementHandler
from typing import List
from ..utils.dependecies import get_current_superadmin
from ..utils.sessiondependencies import get_current_user_profile

router = APIRouter(tags=["User Management"])
handler = UserManagementHandler()

# This router will contain all the protected endpoints
router = APIRouter(
    tags=["User Management"], 
    dependencies=[Depends(get_current_superadmin)]
)

# This router is for the single unprotected endpoint
public_router = APIRouter(tags=["User Management"])

# --- NEW: Router for general authenticated users ---
authenticated_router = APIRouter(
    tags=["User Management"],
    dependencies=[Depends(get_current_user_profile)]
)

handler = UserManagementHandler()

# --- Protected Routes ---

@router.get("/", response_model=list[UserManagementOut])
def list_users():
    return handler.list_users()

@router.get("/{id}", response_model=UserManagementOut)
def get_user(id: str):
    user = handler.get_user(id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/", response_model=UserManagementOut)
def create_user(data: UserManagementCreate):
    return handler.create_user(data)

@router.put("/{id}", response_model=UserManagementOut)
def update_user(id: str, data: UserManagementUpdate):
    updated = handler.update_user(id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="data not found or no data to update")
    return updated

@router.delete("/{id}")
def delete_user(id: str):
    success = handler.delete_user(id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "deleted"}


# --- Public Route ---

@public_router.post("/email/check") # Not restricted by token or role
async def check_email(data: userCheckemail):
    user_exists = handler.check_email(data.email)
    if not user_exists:
        raise HTTPException(status_code=404, detail="you're not registered in dokumprime")
    
    print(not user_exists.get('id_user') )
    
    if not user_exists.get('id_user'):
        update_data = UserManagementUpdate(id_user=data.id_user)
    
        updated_user = handler.update_user(
            id=user_exists['id'], 
            data=update_data           
        )

        if not updated_user:
            raise HTTPException(status_code=400, detail="Failed to update user.")
        
        return {'status': "successful","message":"you're verified"}
    
    elif user_exists.get('id_user'):
        return {'status': "successful","message":"you're verified"}

    

@public_router.get("/roles/", response_model=List[RoleOut])
def get_roles_list():
    """
    Returns a list of all available roles in the system.
    This is a public endpoint.
    """
    return handler.list_roles()

# --- NEW: Endpoint for any authenticated user ---
@authenticated_router.get("/roles/{role_id}", response_model=RoleName)
def get_role_by_id(role_id: str):
    """
    Returns a specific role by its ID.
    Requires any authenticated user.
    """
    return handler.get_role(role_id)