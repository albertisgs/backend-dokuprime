from fastapi import APIRouter, Depends, status
from .handler import TeamHandler
from .schemas import TeamCreate, TeamUpdate, TeamOut, TeamUserCountOut, StatusResponse
from typing import List
from uuid import UUID
# Ganti dengan dependency superadmin Anda
from ..utils.dependecies import get_current_superadmin 

router = APIRouter(
    tags=["Team Management"],
    dependencies=[Depends(get_current_superadmin)] # Lindungi semua endpoint ini
)
handler = TeamHandler()

@router.get("/", response_model=List[TeamOut])
def list_teams():
    return handler.get_all_teams()

@router.post("/", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
def create_team(team_data: TeamCreate):
    return handler.create_team(team_data)

@router.put("/{team_id}", response_model=TeamOut)
def update_team(team_id: UUID, team_data: TeamUpdate):
    return handler.update_team(team_id, team_data)

@router.delete("/{team_id}", response_model=StatusResponse)
def delete_team(team_id: UUID):
    handler.delete_team(team_id)
    return {"status": "success", "message": "Team deleted successfully"}

@router.get("/{team_id}/user-count", response_model=TeamUserCountOut)
def get_user_count_for_team(team_id: UUID):
    return handler.get_team_user_details(team_id)