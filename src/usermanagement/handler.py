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
        # Ambil data pengguna saat ini sebelum melakukan perubahan apa pun
        user_to_update = self.repo.get_by_id(id, team_id)
        if not user_to_update:
            return None # Akan menghasilkan 404 di routes

        # --- BLOK LOGIKA PENJAGAAN BARU ---
        # Cek apakah ada upaya untuk mengubah tim
        if data.id_team and str(data.id_team) != str(user_to_update.get('id_team')):
            current_role_id = user_to_update.get('id_role')
            
            # Cek apakah pengguna saat ini memiliki role
            if current_role_id:
                # Periksa apakah permintaan update juga sekaligus menghapus role
                # `exclude_unset=True` penting untuk tahu field apa saja yang dikirim client
                update_fields = data.model_dump(exclude_unset=True)
                is_role_being_removed = 'id_role' in update_fields and update_fields['id_role'] is None

                # Jika role tidak sedang dihapus, lakukan validasi
                if not is_role_being_removed:
                    raise HTTPException(
                        status_code=400, # Bad Request
                        detail="Cannot change team while user is assigned to a role. Please unassign the role first, then change the team."
                    )
        
        # Cek jika role diubah, pastikan role baru milik tim yang benar
        if data.id_role:
            # Tentukan tim target (tim baru jika diubah, atau tim saat ini jika tidak)
            target_team_id = data.id_team or user_to_update.get('id_team')
            
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
        
        if updated_user and 'id_role' in data.model_dump(exclude_unset=True):
            email = updated_user.get('email')
            account_type = updated_user.get('account_type') # Diperlukan untuk channel yang unik
            
            if email and account_type:
                channel_name = f"user-updates-{email}-{account_type}"
                send_pusher_notification(
                    channel=channel_name,
                    event='role-changed',
                    data={'message': 'Your role or permissions have been updated by an admin.'}
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

    def get_roles_for_team(self, team_id: UUID):
        """Handler untuk mengambil roles berdasarkan team_id."""
        roles = self.repo.get_roles_by_team_id(team_id)
        if not roles:
            return []
        return roles