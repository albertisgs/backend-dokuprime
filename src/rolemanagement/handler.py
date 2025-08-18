# ======================================================================
# 4. FILE BARU: src/rolemanagement/handler.py (DIPERBARUI)
# ======================================================================
from .repository import RoleRepository
from .schemas import RoleCreate, RoleUpdate, VALID_ACCESS_RIGHTS
from fastapi import HTTPException, status
from uuid import UUID
# Import pusher helper
from src.utils.pusher import send_pusher_notification

class RoleHandler:
    def __init__(self):
        self.repo = RoleRepository()

    def _validate_access_rights(self, access_list: list):
        for right in access_list:
            if right not in VALID_ACCESS_RIGHTS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid access right: '{right}'"
                )

    def get_all_roles(self):
        return self.repo.get_all()

    def create_role(self, role_data: RoleCreate):
        self._validate_access_rights(role_data.access)
        return self.repo.create(role_data)

    def update_role(self, role_id: UUID, role_data: RoleUpdate):
        if role_data.access is not None:
            self._validate_access_rights(role_data.access)
        
        updated_role = self.repo.update(role_id, role_data)
        if not updated_role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        
        # Kirim notifikasi Pusher setelah update berhasil
        send_pusher_notification(
            channel='role-updates',
            event='access-changed',
            data={'role_id': str(role_id)}
        )
        
        return updated_role

    def delete_role(self, role_id: UUID):
        # Cek apakah role sedang digunakan sebelum menghapus
        user_count, _ = self.repo.get_user_count_and_names(role_id)
        if user_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete role. It is currently assigned to {user_count} user(s)."
            )
        
        success = self.repo.delete(role_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        return True

    def get_role_user_details(self, role_id: UUID):
        # Pastikan role ada sebelum menghitung
        role = self.repo.get_by_id(role_id)
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        
        count, names = self.repo.get_user_count_and_names(role_id)
        return {"role_id": role_id, "user_count": count, "usernames": names}
