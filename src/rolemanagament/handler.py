# src/rolemanagament/handler.py (Updated & Fixed)

from fastapi import HTTPException, status
from uuid import UUID
from .repository import RoleRepository
from .schemas import RoleCreate, RoleUpdate
from typing import List

class RoleHandler:
    def __init__(self):
        self.repo = RoleRepository()

    def get_all_roles(self, team_id: UUID = None):
        return self.repo.get_all(team_id=team_id)

    def create_role(self, role_data: RoleCreate, team_id: UUID):
        existing_role = self.repo.get_by_name_and_team(role_data.name, team_id)
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role with name '{role_data.name}' already exists in this team."
            )
        
        # Ekstrak permission_ids dari data
        permission_ids = role_data.permission_ids
        
        # Buat role baru di database
        new_role = self.repo.create(role_data, team_id)
        
        # Jika ada permission_ids yang dikirim, langsung tetapkan
        if permission_ids is not None:
            new_role_id = new_role.get('id')
            if new_role_id:
                self.repo.set_permissions_for_role(new_role_id, permission_ids)
        
        # Ambil kembali data role yang sudah lengkap dengan permissions
        final_role_data = self.repo.get_by_id(new_role.get('id'))

        return final_role_data

    def set_permissions(self, role_id: UUID, permission_ids: List[int], team_id: UUID = None):
        role = self.repo.get_by_id(role_id)
        if team_id and (not role or str(role.get('id_team')) != str(team_id)):
            raise HTTPException(status_code=404, detail="Role not found in your team.")
        elif not role:
            raise HTTPException(status_code=404, detail="Role not found.")
            
        try:
            self.repo.set_permissions_for_role(role_id, permission_ids)
            return {"status": "success", "message": "Permissions for the role have been updated."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {e}")

    def delete_role(self, role_id: UUID, team_id: UUID = None):
        role = self.repo.get_by_id(role_id)
        if team_id and (not role or str(role.get('id_team')) != str(team_id)):
            return False
        elif not role:
            return False
        
        # Cek jika role digunakan oleh user
        user_count = self.repo.get_user_count_for_role(role_id)
        if user_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete role. It is currently assigned to {user_count} user(s)."
            )
            
        return self.repo.delete(role_id)
        
    def get_all_permissions(self):
        return self.repo.get_all_permissions()
    

    def update_role(self, role_id: UUID, data: RoleUpdate, team_id: UUID = None):
        role = self.repo.get_by_id(role_id)
        if team_id and (not role or str(role.get('id_team')) != str(team_id)):
            raise HTTPException(status_code=404, detail="Role not found in your team.")
        elif not role:
            raise HTTPException(status_code=404, detail="Role not found.")

        # 1. Siapkan data untuk update nama & deskripsi
        role_details_to_update = data.model_dump(exclude={'permission_ids'}, exclude_unset=True)
        
        # 2. Update nama dan deskripsi jika ada
        if role_details_to_update:
            self.repo.update(role_id, role_details_to_update)

        # 3. Update permissions jika ada
        if data.permission_ids is not None:
            self.repo.set_permissions_for_role(role_id, data.permission_ids)
        # <-- BAGIAN KUNCI: Selalu kembalikan dictionary ini
        return {"status": "success", "message": "Role has been updated successfully."}
    
    # --- TAMBAHKAN FUNGSI BARU INI ---
    def get_role_by_id(self, role_id: UUID, team_id: UUID = None):
        role = self.repo.get_by_id(role_id)
        
        if not role:
            raise HTTPException(status_code=404, detail="Role not found.")

        # Validasi kepemilikan untuk non-superadmin
        if team_id and str(role.get('id_team')) != str(team_id):
            raise HTTPException(status_code=404, detail="Role not found in your team.")
            
        return role
    
    def get_filtered_permissions_for_team(self, team_id: UUID):
        """Mengembalikan daftar permissions yang sudah difilter berdasarkan hak akses tim."""
        team_access_rights = self.repo.get_team_access_rights(team_id)
        all_permissions = self.repo.get_all_permissions()

        if not team_access_rights:
            # Jika tim tidak punya hak akses sama sekali, kembalikan array kosong
            return []

        # Filter permissions: hanya kembalikan permission yang nama modulnya
        # ada di dalam daftar team_access_rights.
        filtered_permissions = [
            p for p in all_permissions 
            if p['name'].split(':')[0] in team_access_rights
        ]
        
        return filtered_permissions

    def get_roles_by_team(self, team_id: UUID):
        """Mengembalikan daftar roles yang dimiliki oleh sebuah tim spesifik."""
        # Kita bisa gunakan ulang fungsi get_all_roles dengan filter team_id
        return self.get_all_roles(team_id=team_id)
