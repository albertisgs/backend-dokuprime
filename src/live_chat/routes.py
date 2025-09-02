# src/live_chat/routes.py (Updated)

from fastapi import APIRouter, Depends, HTTPException, Body
from uuid import UUID
from .handler import LiveChatHandler
# --- PERBAIKAN: Impor schema yang benar ---
from .schemas import ChatSessionRequest, QueueItemOut, ChatSessionOut, AgentMessageRequest
from ..utils.sessiondependencies import get_current_user_profile
from ..utils.dependecies import require_permission

# Router untuk pengguna (meminta sesi)
user_router = APIRouter(
    tags=["Live Chat (User)"],
    dependencies=[Depends(get_current_user_profile)]
)

# Router untuk agen (mengelola sesi)
agent_router = APIRouter(
    tags=["Live Chat (Agent)"],
    dependencies=[Depends(require_permission("agent-dashboard:access"))]
)

handler = LiveChatHandler()

# --- Endpoint untuk Pengguna ---

@user_router.post("/request-session", status_code=201)
def request_session(
    data: ChatSessionRequest,
    current_user: dict = Depends(get_current_user_profile)
):
    user_id = current_user.get("id")
    return handler.request_chat_session(user_id, data)

# --- Endpoint untuk Agen ---

@agent_router.get("/queue", response_model=list[QueueItemOut])
def get_queue():
    """Mengambil daftar semua sesi chat yang sedang dalam antrian ('pending')."""
    return handler.get_agent_queue()

@agent_router.post("/sessions/{session_id}/claim", response_model=ChatSessionOut)
def claim_session(
    session_id: UUID,
    current_user: dict = Depends(get_current_user_profile)
):
    """Seorang agen mengklaim sesi chat dari antrian."""
    agent_id = current_user.get("id")
    agent_name = current_user.get("username")
    print(agent_id)
    print(agent_name)
    return handler.claim_chat_session(session_id, agent_id, agent_name)

@agent_router.post("/sessions/{session_id}/send-message")
def agent_send_message(
    session_id: UUID,
    # --- PERBAIKAN: Gunakan schema yang benar ---
    data: AgentMessageRequest,
    current_user: dict = Depends(get_current_user_profile)
):
    """Agen mengirim pesan dalam sesi chat yang aktif."""
    agent_id = current_user.get("id")
    return handler.send_agent_message(session_id, agent_id, data)

@agent_router.post("/sessions/{session_id}/resolve", status_code=200)
def resolve_session(
    session_id: UUID,
    current_user: dict = Depends(get_current_user_profile)
):
    """Agen menandai sesi sebagai selesai/teratasi."""
    agent_id = current_user.get("id")
    return handler.resolve_session(session_id, agent_id)

