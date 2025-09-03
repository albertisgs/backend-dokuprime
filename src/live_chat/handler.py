# src/live_chat/handler.py (Diperbarui)

from fastapi import HTTPException, status
from uuid import UUID
from .repository import LiveChatRepository
from .schemas import ChatSessionRequest, AgentMessageRequest, UserMessageRequest, AgentStatusRequest, TransferRequest
from ..utils.pusher import send_pusher_notification
from typing import Dict, Any, List
from datetime import datetime

class LiveChatHandler:
    def __init__(self):
        self.repo = LiveChatRepository()

    # --- FUNGSI BARU: Mengelola Status Agen ---
    def set_agent_status(self, agent_id: UUID, data: AgentStatusRequest) -> Dict[str, Any]:
        """Mengatur status agen dan memberitahu dashboard."""
        status = data.status
        updated_agent = self.repo.set_agent_status(agent_id, status)
        if not updated_agent:
            raise HTTPException(status_code=404, detail="Agent not found.")

        # Kirim notifikasi ke channel 'agent-dashboard' bahwa status seorang agen berubah
        send_pusher_notification(
            channel='agent-dashboard',
            event='agent-status-changed',
            data={
                'agent_id': str(updated_agent['id']),
                'status': updated_agent['agent_status']
            }
        )
        return {"status": "success", "agent_id": agent_id, "new_status": status}

    # --- FUNGSI BARU: Untuk Fitur Sesi Persistent ---
    def get_user_sessions(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Mengambil sesi aktif (chatbot/queued/active) yang bisa dilanjutkan oleh user."""
        return self.repo.get_user_active_sessions(user_id)

    def request_chat_session(self, user_id: UUID, data: ChatSessionRequest) -> Dict[str, Any]:
        """Membuat sesi chat baru (jika belum ada) dan langsung memasukkannya ke antrian."""
        # Cek apakah sudah ada agen yang online
        available_agent = self.repo.find_available_agent()
        
        # Jika tidak ada agen online, jangan buat sesi. Beri tahu user.
        if not available_agent:
            raise HTTPException(status_code=400, detail="Saat ini tidak ada agen yang tersedia. Silakan coba lagi nanti.")

        # Ubah status dari 'chatbot' menjadi 'queued'
        new_session = self.repo.create_chat_session(user_id, data.dify_conversation_id, status='queued')
        if not new_session:
            raise HTTPException(status_code=500, detail="Could not create live chat session.")

        # Kirim notifikasi ke channel 'agent-dashboard' bahwa ada sesi baru di antrian
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
        return {"status": "success", "session_id": new_session['id'], "message": "Permintaan chat berhasil dikirim ke antrian."}

    def send_user_message(self, session_id: UUID, user_id: UUID, data: UserMessageRequest):
        """User mengirim pesan ke agent."""
        session = self.repo.get_session_with_messages(session_id)
        if not session or str(session.get('user_id')) != str(user_id):
            raise HTTPException(status_code=403, detail="Sesi tidak valid atau bukan milik Anda.")
            
        if session.get('status') not in ['active', 'queued']:
            raise HTTPException(status_code=403, detail="Tidak dapat mengirim pesan ke sesi yang tidak aktif.")

        new_message = self.repo.add_message(session_id, user_id, 'user', data.text)

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

    def get_agent_queue(self):
        """Mengambil daftar sesi yang sedang menunggu di antrian."""
        return self.repo.get_pending_sessions_for_queue()

    def claim_chat_session(self, session_id: UUID, agent_id: UUID, agent_name: str) -> Dict[str, Any]:
        """Agen mengklaim sesi, mengambil riwayat, dan memberitahu pengguna."""
        claimed_session = self.repo.claim_session(session_id, agent_id)
        if not claimed_session:
            raise HTTPException(status_code=404, detail="Sesi tidak ditemukan, sudah diklaim, atau Anda sedang dalam sesi lain.")

        dify_conversation_id = claimed_session.get('dify_conversation_id')
        dify_history = self.repo.get_dify_history(dify_conversation_id) if dify_conversation_id else []
        
        history_messages = []
        if dify_history:
            for item in dify_history:
                history_messages.append({
                    "id": f"dify-user-{item.get('created_at').isoformat()}",
                    "sender_type": "user", "message_text": item.get('query'),
                    "timestamp": item.get('created_at').isoformat()
                })
                cleaned_answer = item.get('answer', '').replace('<trigger_agent>', '').strip()
                if cleaned_answer:
                    history_messages.append({
                        "id": f"dify-bot-{item.get('created_at').isoformat()}",
                        "sender_type": "bot", "message_text": cleaned_answer,
                        "timestamp": item.get('created_at').isoformat()
                    })

        live_session_data = self.repo.get_session_with_messages(session_id)
        live_messages = live_session_data.get('messages', []) if live_session_data else []

        response_data = claimed_session
        response_data['history'] = history_messages
        response_data['messages'] = live_messages
        
        user_channel = f"user-chat-{claimed_session['user_id']}"
        send_pusher_notification(
            channel=user_channel,
            event='agent-connected',
            data={ 'session_id': str(claimed_session['id']), 'agent_name': agent_name }
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
            "id": new_message['id'],
            "session_id": str(session_id),
            "sender_id": str(agent_id),
            "sender_type": "agent",
            "message_text": text,
            "timestamp": new_message['timestamp'].isoformat()
        }
        send_pusher_notification(session_channel, 'new_message', pusher_data)
        return {"status": "success", "message": new_message}

    # --- FUNGSI BARU: Untuk Transfer Chat ---
    def transfer_chat_session(self, session_id: UUID, from_agent_id: UUID, data: TransferRequest) -> Dict[str, Any]:
        to_agent_id = data.to_agent_id
        
        transferred_session = self.repo.transfer_session(session_id, from_agent_id, to_agent_id)
        if not transferred_session:
            raise HTTPException(status_code=404, detail="Gagal mentransfer sesi. Sesi mungkin tidak aktif atau agen target tidak valid.")

        # Kirim notifikasi ke agen LAMA bahwa transfer berhasil
        send_pusher_notification(
            channel=f'agent-{from_agent_id}',
            event='session-transferred-away',
            data={'session_id': str(session_id), 'message': 'Sesi berhasil ditransfer.'}
        )

        # Kirim notifikasi ke agen BARU bahwa ada sesi baru untuknya
        send_pusher_notification(
            channel=f'agent-{to_agent_id}',
            event='session-transferred-to-you',
            data={'session_id': str(session_id)}
        )
        
        # Kirim notifikasi ke PENGGUNA bahwa agen telah berganti
        user_channel = f"user-chat-{transferred_session['user_id']}"
        send_pusher_notification(
            channel=user_channel,
            event='agent-transferred',
            data={'session_id': str(session_id)} # Frontend bisa mengambil nama agen baru
        )

        return {"status": "success", "message": "Sesi berhasil ditransfer."}

    def resolve_session(self, session_id: UUID, agent_id: UUID, agent_name: str):
        """Agen menutup sesi, membuat transkrip, dan melepaskan agen."""
        # Ambil semua pesan untuk membuat transkrip
        session_data = self.repo.get_session_with_messages(session_id)
        if not session_data or not session_data.get('messages'):
            raise HTTPException(status_code=404, detail="Sesi tidak ditemukan atau tidak ada pesan untuk ditranskrip.")

        # Buat transkrip
        transcript_lines = [f"--- Transkrip Sesi Chat ID: {session_id} ---"]
        transcript_lines.append(f"User: {session_data.get('user_id')}") # Bisa diganti dengan nama user jika ada join
        transcript_lines.append(f"Agen: {agent_name} ({agent_id})")
        transcript_lines.append(f"Dimulai: {session_data.get('claimed_at')}")
        transcript_lines.append("--- Isi Percakapan ---")

        for msg in session_data['messages']:
            sender = "User" if msg['sender_type'] == 'user' else f"Agen ({agent_name})"
            timestamp = msg['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            transcript_lines.append(f"[{timestamp}] {sender}: {msg['message_text']}")
        
        transcript_lines.append(f"--- Sesi Selesai: {datetime.now()} ---")
        final_transcript = "\n".join(transcript_lines)

        # Simpan ke database
        closed_session = self.repo.end_session(session_id, agent_id, final_transcript)
        if not closed_session:
            raise HTTPException(status_code=404, detail="Sesi aktif tidak ditemukan untuk agen ini.")

        user_channel = f"user-chat-{closed_session['user_id']}"
        send_pusher_notification(
            channel=user_channel,
            event='session-resolved',
            data={'session_id': str(session_id)}
        )
        return {"status": "success", "message": "Sesi telah diselesaikan dan transkrip disimpan."}

    # --- FUNGSI BARU ---
    def get_canned_responses(self, agent_team_id: UUID) -> List[Dict[str, Any]]:
        """Mengambil pesan cepat untuk tim agen."""
        if not agent_team_id:
            return []
        return self.repo.get_canned_responses_for_team(agent_team_id)
    
    # Ganti fungsi get_session_history di src/live_chat/handler.py dengan yang ini

    def get_session_history(self, session_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """Handler untuk mengambil riwayat lengkap sesi untuk pengguna."""
        session_data = self.repo.get_session_history_for_user(session_id, user_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Sesi tidak ditemukan atau Anda tidak memiliki akses.")

        dify_conversation_id = session_data.get('dify_conversation_id')
        dify_history = self.repo.get_dify_history(dify_conversation_id) if dify_conversation_id else []
        
        history_messages = []
        if dify_history:
            for item in dify_history:
                # --- PERBAIKAN DI SINI: Tambahkan session_id ---
                history_messages.append({
                    "id": f"dify-user-{item.get('created_at').isoformat()}",
                    "session_id": session_id, # <--- TAMBAHKAN INI
                    "sender_id": user_id,     # <--- TAMBAHKAN INI (opsional tapi bagus)
                    "sender_type": "user", 
                    "message_text": item.get('query'),
                    "timestamp": item.get('created_at')
                })
                cleaned_answer = item.get('answer', '').replace('<trigger_agent>', '').strip()
                if cleaned_answer:
                    # --- PERBAIKAN DI SINI: Tambahkan session_id ---
                    history_messages.append({
                        "id": f"dify-bot-{item.get('created_at').isoformat()}",
                        "session_id": session_id, # <--- TAMBAHKAN INI
                        "sender_id": None,        # <--- TAMBAHKAN INI
                        "sender_type": "bot", 
                        "message_text": cleaned_answer,
                        "timestamp": item.get('created_at')
                    })
        
        live_messages = session_data.get('messages', [])
        
        all_messages = history_messages + live_messages
        all_messages.sort(key=lambda x: x['timestamp'])

        response_data = session_data
        response_data['messages'] = all_messages
        response_data['history'] = [] 
        
        return response_data
    
   
    def get_my_active_session(self, agent_id: UUID):
        """Handler untuk agen mengambil sesi aktif yang sedang ditanganinya."""
        # Langkah 1: Temukan sesi aktif dasar untuk agen ini
        active_session = self.repo.get_agent_active_session_by_id(agent_id)
        
        if not active_session:
            return None # Jika tidak ada sesi, kembalikan None

        session_id = active_session['id']
        
        # Langkah 2: Ambil data sesi lengkap termasuk pesan live chat
        full_session_data = self.repo.get_session_with_messages(session_id)
        if not full_session_data:
            return None

        # Langkah 3: Ambil riwayat dari Dify
        dify_conversation_id = full_session_data.get('dify_conversation_id')
        dify_history = self.repo.get_dify_history(dify_conversation_id) if dify_conversation_id else []
        
        history_messages = []
        if dify_history:
            for item in dify_history:
                history_messages.append({
                    "id": f"dify-user-{item.get('created_at').isoformat()}",
                    "sender_type": "user", "message_text": item.get('query'),
                    "timestamp": item.get('created_at').isoformat()
                })
                cleaned_answer = item.get('answer', '').replace('<trigger_agent>', '').strip()
                if cleaned_answer:
                    history_messages.append({
                        "id": f"dify-bot-{item.get('created_at').isoformat()}",
                        "sender_type": "bot", "message_text": cleaned_answer,
                        "timestamp": item.get('created_at').isoformat()
                    })

        # Langkah 4: Gabungkan semua data menjadi satu respons yang konsisten
        response_data = full_session_data
        # Tambahkan user_name dari query pertama agar tersedia di frontend
        response_data['user_name'] = active_session.get('user_name') 
        response_data['history'] = history_messages
        # 'messages' sudah ada dari full_session_data
        
        return response_data