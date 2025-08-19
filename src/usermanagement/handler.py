# src/usermanagement/handler.py (Updated)

from .repository import UserManagementRepository
from .schemas import UserManagementCreate, UserManagementUpdate, userCheckemail
from fastapi import HTTPException
from src.utils.pusher import send_pusher_notification
from uuid import UUID

class UserManagementHandler:
    def __init__(self):
        self.repo = UserManagementRepository()

    # --- PERUBAHAN ---
    # Menambahkan parameter opsional team_id
    def list_users(self, team_id: UUID = None):
        return self.repo.list_all(team_id=team_id)

    # --- PERUBAHAN ---
    # Menambahkan parameter opsional team_id
    def get_user(self, id: str, team_id: UUID = None):
        return self.repo.get_by_id(id, team_id=team_id)

    def create_user(self, data: UserManagementCreate):
        # Cek apakah role yang diassign ada di dalam tim yang sama
        if data.id_role:
            role = self.repo.get_role_by_id(data.id_role)
            if not role or str(role.get('id_team')) != str(data.id_team):
                raise HTTPException(status_code=400, detail="Invalid Role ID for the selected team.")
        return self.repo.create(data)

    # --- PERUBAHAN ---
    # Menambahkan parameter opsional team_id
    def update_user(self, id: str, data: UserManagementUpdate, team_id: UUID = None):
        # Verifikasi bahwa user yang akan diupdate ada di dalam tim (jika diakses oleh Admin Tim)
        if team_id:
            user_to_update = self.repo.get_by_id(id, team_id)
            if not user_to_update:
                return None # Akan menghasilkan 404 di routes

        # Cek jika role diubah, pastikan role baru milik tim yang benar
        if data.id_role:
            # Dapatkan tim dari user yang akan diupdate
            target_user = self.repo.get_by_id(id) # get user tanpa filter tim
            if not target_user:
                raise HTTPException(status_code=404, detail="User to update not found.")
            target_team_id = target_user.get('id_team')
            
            role = self.repo.get_role_by_id(data.id_role)
            if not role or str(role.get('id_team')) != str(target_team_id):
                raise HTTPException(status_code=400, detail="Invalid Role ID for the user's team.")

        updated_user = self.repo.update(id, data)
        
        if updated_user and data.id_team:
            email = updated_user.get('email')
            account_type = updated_user.get('account_type')
            
            if email and account_type:
                channel_name = f"user-updates-{email}-{account_type}"
                send_pusher_notification(
                    channel=channel_name,
                    event='team-changed',
                    data={'message': 'Your team assignment has been updated by an admin.'}
                )
        return updated_user

    # --- PERUBAHAN ---
    # Menambahkan parameter opsional team_id
    def delete_user(self, id: str, team_id: UUID = None):
        # Jika team_id ada, verifikasi dulu user ada di tim itu sebelum menghapus
        if team_id:
            user_to_delete = self.repo.get_by_id(id, team_id)
            if not user_to_delete:
                return False # Akan menghasilkan 404 di routes
        return self.repo.delete(id)
    
    # --- PERUBAHAN ---
    # Memindahkan logika dari routes ke handler
    async def check_email_and_update(self, data: userCheckemail):
        user_exists = self.repo.check(data.email)
        if not user_exists:
            raise HTTPException(status_code=404, detail="you're not registered in dokumprime")
        
        if not user_exists.get('id_user'):
            update_data = UserManagementUpdate(id_user=data.id_user)
            updated_user = self.update_user(id=user_exists['id'], data=update_data)
            if not updated_user:
                raise HTTPException(status_code=400, detail="Failed to update user.")
        
        return {'status': "successful", "message": "you're verified"}

    def list_teams(self):
        return self.repo.list_teams()
    
    def get_team(self, team_id: str):
        team = self.repo.get_team_by_id(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        return team
