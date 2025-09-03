# src/live_chat/routes.py (Diperbarui)

from fastapi import APIRouter, Depends, HTTPException, Body, Query
from uuid import UUID
from typing import List, Optional
from .handler import LiveChatHandler
from .schemas import (
    ChatSessionRequest, QueueItemOut, AgentHistoryDetailOut, AgentMessageRequest,
    UserMessageRequest, AgentStatusRequest, UserSessionOut, CannedResponseOut,
    TransferRequest, AgentHistoryItemOut,
)
from ..utils.sessiondependencies import get_current_user_profile
from ..utils.dependecies import require_permission

# --- Router untuk Pengguna (User-facing endpoints) ---
user_router = APIRouter(
    prefix="/live-chat",
    tags=["Live Chat (User)"],
    dependencies=[Depends(get_current_user_profile)]
)

# --- Router untuk Agen (Agent-facing endpoints) ---
agent_router = APIRouter(
    prefix="/live-chat/agent",
    tags=["Live Chat (Agent)"],
    dependencies=[Depends(require_permission("agent-dashboard:access"))]
)

handler = LiveChatHandler()

# =================================================================
# --- ENDPOINTS UNTUK PENGGUNA (USER) ---
# =================================================================

@user_router.get("/sessions", response_model=List[UserSessionOut])
def get_user_sessions(current_user: dict = Depends(get_current_user_profile)):
    """(BARU) Mengambil daftar sesi aktif yang bisa dilanjutkan oleh pengguna."""
    user_id = current_user.get("id")
    return handler.get_user_sessions(user_id)

@user_router.post("/request-session", status_code=201)
def request_session(
    data: ChatSessionRequest,
    current_user: dict = Depends(get_current_user_profile)
):
    """Pengguna meminta sesi live chat baru dengan agen."""
    user_id = current_user.get("id")
    return handler.request_chat_session(user_id, data)

@user_router.post("/sessions/{session_id}/send-message")
def user_send_message(
    session_id: UUID,
    data: UserMessageRequest,
    current_user: dict = Depends(get_current_user_profile)
):
    """Pengguna mengirim pesan dalam sesi chat yang sedang berjalan."""
    user_id = current_user.get("id")
    return handler.send_user_message(session_id, user_id, data)

@user_router.get("/sessions/{session_id}/history", response_model=AgentHistoryDetailOut)
def get_session_history(
    session_id: UUID,
    current_user: dict = Depends(get_current_user_profile)
):
    """(BARU) Pengguna mengambil riwayat lengkap dari sesi spesifik miliknya."""
    user_id = current_user.get("id")
    return handler.get_session_history(session_id, user_id)
# =================================================================
# --- ENDPOINTS UNTUK AGEN (AGENT) ---
# =================================================================

@agent_router.put("/status", status_code=200)
def set_agent_status(
    data: AgentStatusRequest,
    current_user: dict = Depends(get_current_user_profile)
):
    """(BARU) Agen mengatur status mereka (online, away, offline)."""
    agent_id = current_user.get("id")
    return handler.set_agent_status(agent_id, data)

@agent_router.get("/queue", response_model=List[QueueItemOut])
def get_queue():
    """Mengambil daftar semua sesi chat yang sedang dalam antrian ('queued')."""
    return handler.get_agent_queue()

@agent_router.post("/sessions/{session_id}/claim", response_model=AgentHistoryDetailOut)
def claim_session(
    session_id: UUID,
    current_user: dict = Depends(get_current_user_profile)
):
    """Seorang agen mengklaim sesi chat dari antrian."""
    agent_id = current_user.get("id")
    agent_name = current_user.get("username")
    return handler.claim_chat_session(session_id, agent_id, agent_name)

@agent_router.post("/sessions/{session_id}/send-message")
def agent_send_message(
    session_id: UUID,
    data: AgentMessageRequest,
    current_user: dict = Depends(get_current_user_profile)
):
    """Agen mengirim pesan dalam sesi chat yang aktif."""
    agent_id = current_user.get("id")
    return handler.send_agent_message(session_id, agent_id, data)

@agent_router.post("/sessions/{session_id}/transfer", status_code=200)
def transfer_session(
    session_id: UUID,
    data: TransferRequest,
    current_user: dict = Depends(get_current_user_profile)
):
    """(BARU) Agen mentransfer sesi yang sedang ditangani ke agen lain."""
    from_agent_id = current_user.get("id")
    return handler.transfer_chat_session(session_id, from_agent_id, data)


@agent_router.post("/sessions/{session_id}/resolve", status_code=200)
def resolve_session(
    session_id: UUID,
    current_user: dict = Depends(get_current_user_profile)
):
    """Agen menandai sesi sebagai selesai/teratasi dan menyimpan transkrip."""
    agent_id = current_user.get("id")
    agent_name = current_user.get("username")
    return handler.resolve_session(session_id, agent_id, agent_name)

@agent_router.get("/canned-responses", response_model=List[CannedResponseOut])
def get_canned_responses(current_user: dict = Depends(get_current_user_profile)):
    """(BARU) Mengambil daftar pesan cepat untuk tim agen."""
    agent_team_id = current_user.get("id_team")
    return handler.get_canned_responses(agent_team_id)

@agent_router.get("/my-session", response_model=Optional[AgentHistoryDetailOut])
def get_my_active_session(current_user: dict = Depends(get_current_user_profile)):
    """(BARU) Agen mengambil sesi aktifnya saat ini (jika ada) untuk persistensi UI."""
    agent_id = current_user.get("id")
    return handler.get_my_active_session(agent_id)

@agent_router.get("/history", response_model=List[AgentHistoryItemOut])
def get_history_list(
    current_user: dict = Depends(get_current_user_profile),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """(BARU) Agen mengambil daftar sesi yang telah diselesaikannya."""
    agent_id = current_user.get("id")
    return handler.get_agent_chat_history(agent_id, limit, offset)

@agent_router.get("/history/{session_id}", response_model=AgentHistoryDetailOut)
def get_history_detail(
    session_id: UUID,
    current_user: dict = Depends(get_current_user_profile)
):
    """(BARU) Agen mengambil detail dan transkrip dari satu sesi riwayat."""
    agent_id = current_user.get("id")
    # Kita gunakan response model AgentHistoryDetailOut karena sudah mencakup semua data yang dibutuhkan (termasuk transkrip)
    return handler.get_agent_chat_transcript(session_id, agent_id)