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
        updated_user = self.repo.update(id, data)
        
        # --- CHANGE HERE ---
        if updated_user and data.id_team:
            email = updated_user.get('email')
            account_type = updated_user.get('account_type')
            
            if email and account_type:
                channel_name = f"user-updates-{email}-{account_type}"
                
                send_pusher_notification(
                    channel=channel_name,
                    # --- CHANGE HERE ---
                    event='team-changed',
                    data={'message': 'Your team assignment has been updated by an admin.'}
                )
        return updated_user

    def delete_user(self, id: str):
        return self.repo.delete(id)
    
    def check_email(self, email:str):
        return self.repo.check(email)

     # --- CHANGE HERE ---
    def list_teams(self):
        return self.repo.list_teams()
    
    def get_team(self, team_id: str):
        team = self.repo.get_team_by_id(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        return team