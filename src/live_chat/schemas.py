# src/live_chat/schemas.py (Diperbarui)

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List, Optional, Literal

# --- SKEMA BARU: Untuk request dari agen saat mengubah status ---
class AgentStatusRequest(BaseModel):
    status: Literal['online', 'away', 'offline']

# --- SKEMA BARU: Untuk request dari agen saat mentransfer chat ---
class TransferRequest(BaseModel):
    to_agent_id: UUID

# --- SKEMA BARU: Untuk menampilkan daftar sesi aktif milik user ---
class UserSessionOut(BaseModel):
    id: UUID
    status: str
    created_at: datetime
    agent_name: Optional[str] = None

    class Config:
        from_attributes = True
        
# --- SKEMA BARU: Untuk menampilkan pesan cepat (canned response) ---
class CannedResponseOut(BaseModel):
    id: UUID
    shortcut: str
    message_text: str

    class Config:
        from_attributes = True

# Schema untuk request dari user (frontend) saat meminta sesi live chat
class ChatSessionRequest(BaseModel):
    dify_conversation_id: UUID

# Schema untuk pesan yang dikirim oleh agen
class AgentMessageRequest(BaseModel):
    message_text: str
    
# Schema untuk pesan yang dikirim oleh user ke agent
class UserMessageRequest(BaseModel):
    text: str

# Schema untuk menampilkan pesan individual dalam sesi
# Schema untuk menampilkan pesan individual dalam sesi
class LiveChatMessageOut(BaseModel):
    id: str
    session_id: UUID
    sender_id: Optional[UUID] = None 
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
    dify_conversation_id: Optional[UUID] = None
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
        
        
class AgentHistoryItemOut(BaseModel):
    id: UUID
    user_name: Optional[str] = None
    ended_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# --- SKEMA BARU: Untuk detail lengkap riwayat chat (termasuk transkrip) ---
class AgentHistoryDetailOut(AgentHistoryItemOut):
    transcript: Optional[str] = None
    
    
class AgentActiveSessionOut(ChatSessionOut):
    user_name: Optional[str] = None
    
class ChatSessionInitiateRequest(BaseModel):
    dify_conversation_id: UUID
    
class AgentChatRequest(BaseModel):
    live_chat_session_id: UUID