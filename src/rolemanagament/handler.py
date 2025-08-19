# src/rolemanagament/handler.py (Updated)

from fastapi import HTTPException, status
from uuid import UUID
from .repository import RoleRepository
from .schemas import RoleCreate
from typing import List 

class RoleHandler:
    def __init__(self):
        self.repo = RoleRepository()

    # --- PERUBAHAN ---
    # Menambahkan parameter opsional team_id
    def get_all_roles(self, team_id: UUID = None):
        return self.repo.get_all(team_id=team_id)

    # --- PERUBAHAN ---
    # Menambahkan parameter wajib team_id
    def create_role(self, role_data: RoleCreate, team_id: UUID):
        # Pastikan role dengan nama yang sama belum ada di tim yang sama
        existing_role = self.repo.get_by_name_and_team(role_data.name, team_id)
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role with name '{role_data.name}' already exists in this team."
            )
        return self.repo.create(role_data, team_id)
        
    # --- PERUBAHAN ---
    # Menambahkan parameter team_id untuk verifikasi
    def add_permission(self, role_id: UUID, permission_id: int, team_id: UUID):
        # Verifikasi bahwa role ini milik tim yang benar
        role = self.repo.get_by_id(role_id)
        if not role or str(role.get('id_team')) != str(team_id):
            raise HTTPException(status_code=404, detail="Role not found in your team.")
        
        success = self.repo.add_permission_to_role(role_id, permission_id)
        return {"status": "success", "message": "Permission added to role."}

    # --- PERUBAHAN ---
    # Menambahkan parameter team_id untuk verifikasi
    def remove_permission(self, role_id: UUID, permission_id: int, team_id: UUID):
        role = self.repo.get_by_id(role_id)
        if not role or str(role.get('id_team')) != str(team_id):
            raise HTTPException(status_code=404, detail="Role not found in your team.")

        success = self.repo.remove_permission_from_role(role_id, permission_id)
        if not success:
            raise HTTPException(status_code=404, detail="Role or Permission link not found.")
        return {"status": "success", "message": "Permission removed from role."}
        
    def get_all_permissions(self):
        return self.repo.get_all_permissions()
    
    # --- PERUBAHAN ---
    # Menambahkan parameter team_id untuk verifikasi
    def set_permissions(self, role_id: UUID, permission_ids: List[int], team_id: UUID):
        role = self.repo.get_by_id(role_id)
        if not role or str(role.get('id_team')) != str(team_id):
            raise HTTPException(status_code=404, detail="Role not found in your team.")
            
        try:
            self.repo.set_permissions_for_role(role_id, permission_ids)
            return {"status": "success", "message": "Permissions for the role have been updated."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {e}")
