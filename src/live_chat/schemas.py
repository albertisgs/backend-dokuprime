# src/live_chat/schemas.py

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List, Optional

# Schema untuk request dari user (frontend) saat meminta sesi live chat
class ChatSessionRequest(BaseModel):
    dify_conversation_id: UUID

# Schema untuk pesan yang dikirim oleh agen
class AgentMessageRequest(BaseModel):
    message_text: str

# --- TAMBAHAN BARU ---
# Schema untuk menampilkan pesan individual dalam sesi
class LiveChatMessageOut(BaseModel):
    id: UUID
    session_id: UUID
    sender_id: UUID
    sender_type: str
    message_text: str
    timestamp: datetime

    class Config:
        from_attributes = True

# Schema untuk menampilkan data sesi lengkap, termasuk riwayat dan pesan baru
class ChatSessionOut(BaseModel):
    id: UUID
    user_id: UUID
    agent_id: Optional[UUID] = None
    dify_conversation_id: UUID
    status: str
    created_at: datetime
    claimed_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    messages: List[LiveChatMessageOut] = []
    history: List[dict] = [] # Untuk riwayat dari Dify

    class Config:
        from_attributes = True

# Schema untuk item dalam antrian agen
class QueueItemOut(BaseModel):
    session_id: UUID
    user_name: str
    created_at: datetime
    status: str

    class Config:
        from_attributes = True

