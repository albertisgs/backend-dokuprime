# src/live_chat/handler.py (Updated)

from fastapi import HTTPException, status
from uuid import UUID
from .repository import LiveChatRepository
from .schemas import ChatSessionRequest, AgentMessageRequest, UserMessageRequest
from ..utils.pusher import send_pusher_notification
from typing import Dict, Any

class LiveChatHandler:
    def __init__(self):
        self.repo = LiveChatRepository()

    def request_chat_session(self, user_id: UUID, data: ChatSessionRequest) -> Dict[str, Any]:
        """Membuat sesi chat baru dan memberitahu agen yang tersedia."""
        new_session = self.repo.create_chat_session(user_id, data.dify_conversation_id)
        if not new_session:
            raise HTTPException(status_code=500, detail="Could not create live chat session.")

        # Kirim notifikasi ke channel 'agent-dashboard' bahwa ada sesi baru
        send_pusher_notification(
            channel='agent-dashboard',
            event='new-pending-session',
            data={
                'session_id': str(new_session['id']),
                'user_id': str(new_session['user_id']),
                'status': new_session['status'],
                'created_at': new_session['created_at'].isoformat()
            }
        )
        return {"status": "success", "session_id": new_session['id']}
    
    # --- TAMBAHKAN FUNGSI BARU INI ---
    def send_user_message(self, session_id: UUID, user_id: UUID, data: UserMessageRequest):
        """User mengirim pesan ke agent."""
        # Verifikasi dulu apakah sesi ini milik user tersebut dan aktif
        session = self.repo.get_session_with_messages(session_id)
        if not session or str(session.get('user_id')) != str(user_id) or session.get('status') != 'active':
            raise HTTPException(status_code=403, detail="Cannot send message to this session.")

        new_message = self.repo.add_message(session_id, user_id, 'user', data.text)

        # Kirim notifikasi ke agent melalui Pusher
        session_channel = f"chat-session-{session_id}"
        pusher_data = {
            "id": new_message['id'],
            "session_id": str(session_id),
            "sender_id": str(user_id),
            "sender_type": "user",
            "message_text": data.text,
            "timestamp": new_message['timestamp'].isoformat()
        }
        send_pusher_notification(session_channel, 'new_message', pusher_data)
        
        return {"status": "success", "message": new_message}
    # --- BATAS PENAMBAHAN ---

    def get_agent_queue(self):
        """Mengambil daftar sesi yang sedang menunggu di antrian."""
        return self.repo.get_pending_sessions_for_queue()

    def claim_chat_session(self, session_id: UUID, agent_id: UUID, agent_name: str) -> Dict[str, Any]:
        """Agen mengklaim sesi, mengambil riwayat, dan memberitahu pengguna."""
        claimed_session = self.repo.claim_session(session_id, agent_id)
        if not claimed_session:
            raise HTTPException(status_code=404, detail="Session not found or already claimed.")

        dify_conversation_id = claimed_session.get('dify_conversation_id')
        dify_history = self.repo.get_dify_history(dify_conversation_id)
        history_messages = []
        if dify_history:
            for item in dify_history:
                history_messages.append({
                    "sender_type": "user",
                    "message_text": item.get('query'),
                    "timestamp": item.get('created_at').isoformat()
                })
                cleaned_answer = item.get('answer', '').replace('<trigger_agent>', '').strip()
                if cleaned_answer:
                    history_messages.append({
                        "sender_type": "bot",
                        "message_text": cleaned_answer,
                        "timestamp": item.get('created_at').isoformat()
                    })

        live_messages = self.repo.get_session_with_messages(session_id)

        response_data = claimed_session
        response_data['history'] = history_messages
        response_data['messages'] = live_messages.get('messages', []) if live_messages else []

        # FIX: Menggunakan channel yang benar dengan user_id dari sesi
        user_channel = f"user-chat-{claimed_session['user_id']}"
        send_pusher_notification(
            channel=user_channel,
            event='agent-connected',
            data={
                'session_id': str(claimed_session['id']),
                'agent_name': agent_name
            }
        )
        
        send_pusher_notification(
            channel='agent-dashboard',
            event='session-claimed',
            data={'session_id': str(session_id)}
        )

        return response_data 

    def send_agent_message(self, session_id: UUID, agent_id: UUID, data: AgentMessageRequest):
        """Agen mengirim pesan ke pengguna."""
        text = data.message_text
        new_message = self.repo.add_message(session_id, agent_id, 'agent', text)

        session_channel = f"chat-session-{session_id}"
        pusher_data = {
            "id": new_message['id'], # Menyertakan ID pesan untuk key yang unik di frontend
            "session_id": str(session_id),
            "sender_id": str(agent_id),
            "sender_type": "agent",
            "message_text": text,
            "timestamp": new_message['timestamp'].isoformat()
        }
        send_pusher_notification(session_channel, 'new_message', pusher_data)
        return {"status": "success", "message": new_message}

    def resolve_session(self, session_id: UUID, agent_id: UUID):
        """Agen menutup sesi sebagai 'resolved'."""
        closed_session = self.repo.end_session(session_id, agent_id)
        if not closed_session:
            raise HTTPException(status_code=404, detail="Active session not found for this agent.")

        # FIX: Menggunakan channel dan event yang benar
        user_channel = f"user-chat-{closed_session['user_id']}"
        send_pusher_notification(
            channel=user_channel,
            event='session-resolved', # Mengirim 'session-resolved'
            data={'session_id': str(session_id)}
        )
        return {"status": "success", "message": "Session has been resolved."}