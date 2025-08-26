# src/notifications/schemas.py
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import List, Literal, Optional

# Skema untuk membuat notifikasi (dari admin)
class NotificationCreate(BaseModel):
    title: str
    message: str
    target_type: Literal['all', 'team', 'user']
    target_id: Optional[UUID] = None # Wajib jika tipe 'team' atau 'user'
    link_to: Optional[str] = None

# Skema untuk menampilkan notifikasi ke pengguna
class NotificationOut(BaseModel):
    id: UUID
    notification_id: UUID
    title: str
    message: str
    created_at: datetime
    is_read: bool
    link_to: Optional[str] = None
    
    class Config:
        from_attributes = True

# Skema untuk response daftar notifikasi
class NotificationListResponse(BaseModel):
    unread_count: int
    notifications: List[NotificationOut]