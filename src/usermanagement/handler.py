from .repository import UserManagementRepository
from .schemas import UserManagementCreate, UserManagementUpdate
from fastapi import HTTPException
from src.utils.pusher import send_pusher_notification

class UserManagementHandler:
    def __init__(self):
        self.repo = UserManagementRepository()

    def list_users(self):
        return self.repo.list_all()

    def get_user(self, id: str):
        return self.repo.get_by_id(id)

    def create_user(self, data: UserManagementCreate):
        return self.repo.create(data)

    def update_user(self, id: str, data: UserManagementUpdate):
        # Lakukan update seperti biasa
        updated_user = self.repo.update(id, data)
        
        # --- PERUBAHAN DI SINI ---
        # Jika update berhasil dan role diubah, kirim notifikasi.
        if updated_user and data.id_role:
            email = updated_user.get('email')
            account_type = updated_user.get('account_type')
            
            if email and account_type:
                # Buat nama channel yang unik untuk pengguna ini
                channel_name = f"user-updates-{email}-{account_type}"
                
                send_pusher_notification(
                    channel=channel_name,
                    event='role-changed',
                    data={'message': 'Your user role has been updated by an admin.'}
                )

        return updated_user

    def delete_user(self, id: str):
        return self.repo.delete(id)
    
    def check_email(self, email:str):
        return self.repo.check(email)

    def list_roles(self):
        return self.repo.list_roles()
    
    def get_role(self, role_id: str):
        role = self.repo.get_role_by_id(role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        return role