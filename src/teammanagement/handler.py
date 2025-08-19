# ======================================================================
# 4. FILE BARU: src/teammanagement/handler.py (DIPERBARUI)
# ======================================================================
from .repository import TeamRepository
from .schemas import TeamCreate, TeamUpdate, VALID_ACCESS_RIGHTS
from fastapi import HTTPException, status
from uuid import UUID
# Import pusher helper
from src.utils.pusher import send_pusher_notification

class TeamHandler:
    def __init__(self):
        self.repo = TeamRepository()

    def _validate_access_rights(self, access_list: list):
        for right in access_list:
            if right not in VALID_ACCESS_RIGHTS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid access right: '{right}'"
                )

    def get_all_teams(self):
        return self.repo.get_all()

    def create_team(self, team_data: TeamCreate):
        self._validate_access_rights(team_data.access)
        return self.repo.create(team_data)

    def update_team(self, team_id: UUID, team_data: TeamUpdate):
        if team_data.access is not None:
            self._validate_access_rights(team_data.access)
        
        updated_team = self.repo.update(team_id, team_data)
        if not updated_team:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
        
        # Kirim notifikasi Pusher setelah update berhasil
        send_pusher_notification(
            channel='team-updates',
            event='access-changed',
            data={'team_id': str(team_id)}
        )
        
        return updated_team

    def delete_team(self, team_id: UUID):
        # Cek apakah team sedang digunakan sebelum menghapus
        user_count, _ = self.repo.get_user_count_and_names(team_id)
        if user_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete team. It is currently assigned to {user_count} user(s)."
            )
        
        success = self.repo.delete(team_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
        return True

    def get_team_user_details(self, team_id: UUID):
        # Pastikan team ada sebelum menghitung
        team = self.repo.get_by_id(team_id)
        if not team:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
        
        count, names = self.repo.get_user_count_and_names(team_id)
        return {"team_id": team_id, "user_count": count, "usernames": names}
