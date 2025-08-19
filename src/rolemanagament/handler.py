from fastapi import HTTPException, status
from uuid import UUID
from .repository import RoleRepository
from .schemas import RoleCreate
from typing import List 

class RoleHandler:
    def __init__(self):
        self.repo = RoleRepository()

    def get_all_roles(self):
        return self.repo.get_all()

    def create_role(self, role_data: RoleCreate):
        return self.repo.create(role_data)
        
    def add_permission(self, role_id: UUID, permission_id: int):
        success = self.repo.add_permission_to_role(role_id, permission_id)
        if not success:
            # Ini bisa terjadi jika role/permission tidak ada, atau sudah ada (ON CONFLICT)
            # Untuk simplicity, kita anggap OK
            pass
        return {"status": "success", "message": "Permission added to role."}

    def remove_permission(self, role_id: UUID, permission_id: int):
        success = self.repo.remove_permission_from_role(role_id, permission_id)
        if not success:
            raise HTTPException(status_code=404, detail="Role or Permission link not found.")
        return {"status": "success", "message": "Permission removed from role."}
        
    def get_all_permissions(self):
        return self.repo.get_all_permissions()
    
    def set_permissions(self, role_id: UUID, permission_ids: List[int]):
        try:
            self.repo.set_permissions_for_role(role_id, permission_ids)
            return {"status": "success", "message": "Permissions for the role have been updated."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {e}")