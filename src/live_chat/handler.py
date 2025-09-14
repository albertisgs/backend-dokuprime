# src/live_chat/handler.py (Diperbarui)

from fastapi import HTTPException, status
from uuid import UUID
from .repository import LiveChatRepository
from .schemas import ChatSessionRequest, AgentMessageRequest, UserMessageRequest, AgentStatusRequest, TransferRequest, ChatSessionInitiateRequest
from ..utils.pusher import send_pusher_notification
from typing import Dict, Any, List
from datetime import datetime
import json

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

    def _get_full_session_details(self, session_id: UUID) -> Dict[str, Any]:
        """Mengambil semua detail sesi, termasuk riwayat Dify dan pesan live chat."""
        
        session_data = self.repo.get_session_with_messages(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Sesi tidak ditemukan.")

        dify_conversation_id = session_data.get('dify_conversation_id')
        
        # --- DEBUGGING LOG ---
        print(f"--- Debugging Sesi {session_id} ---")
        print(f"Dify Conversation ID: {dify_conversation_id}")
        
        dify_history = self.repo.get_dify_history(dify_conversation_id) if dify_conversation_id else []
        
        # --- DEBUGGING LOG ---
        print("Riwayat Mentah dari Dify:")
        print(json.dumps(dify_history, indent=2, default=str))

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
        
        # --- DEBUGGING LOG ---
        print("\nRiwayat yang Sudah Diformat untuk Frontend:")
        print(json.dumps(history_messages, indent=2, default=str))

        live_messages = session_data.get('messages', [])
        
        # --- DEBUGGING LOG ---
        print("\nPesan Live dari Database:")
        print(json.dumps(live_messages, indent=2, default=str))

        response_data = session_data
        response_data['history'] = history_messages
        response_data['messages'] = live_messages
        
        return response_data
    
    # --- FUNGSI BARU: Untuk Fitur Sesi Persistent ---
    def get_user_sessions(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Mengambil sesi aktif (chatbot/queued/active) yang bisa dilanjutkan oleh user."""
        return self.repo.get_user_active_sessions(user_id)

    def request_chat_session(self, live_chat_session_id: UUID) -> Dict[str, Any]:
        """Mengubah status sesi dari 'chatbot' menjadi 'queued'."""
        available_agent = self.repo.find_available_agent()
        if not available_agent:
            raise HTTPException(status_code=400, detail="Saat ini tidak ada agen yang tersedia. Silakan coba lagi nanti.")

        # --- PERUBAHAN LOGIKA: Update status, bukan membuat baru ---
        updated_session = self.repo.update_session_status(live_chat_session_id, 'queued')
        if not updated_session:
            raise HTTPException(status_code=404, detail="Live chat session not found.")

        send_pusher_notification(
            channel='agent-dashboard',
            event='new-pending-session',
            data={
                'session_id': str(updated_session['id']),
                'user_id': str(updated_session['user_id']),
                'status': updated_session['status'],
                'created_at': updated_session['created_at'].isoformat()
            }
        )
        return {"status": "success", "session_id": updated_session['id'], "message": "Permintaan chat berhasil dikirim ke antrian."}
    
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

        # Gunakan fungsi helper untuk mendapatkan semua detail
        response_data = self._get_full_session_details(session_id)
        
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


    def get_session_history(self, session_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """
        Handler untuk mengambil riwayat lengkap sesi untuk pengguna,
        menggabungkan riwayat Dify dan pesan live secara akurat.
        """
        # 1. Ambil data sesi utama dan pesan live dari DB lokal
        session_data = self.repo.get_session_history_for_user(session_id, user_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Sesi tidak ditemukan atau Anda tidak memiliki akses.")

        # 2. Ambil riwayat percakapan dari Dify jika ada
        dify_conversation_id = session_data.get('dify_conversation_id')
        dify_history = self.repo.get_dify_history(dify_conversation_id) if dify_conversation_id else []
        
        # 3. Format riwayat Dify menjadi struktur pesan yang konsisten
        history_messages = []
        if dify_history:
            for item in dify_history:
                # Pesan dari pengguna ke bot
                history_messages.append({
                    "id": f"dify-user-{item.get('created_at').isoformat()}",
                    "session_id": session_id,
                    "sender_id": user_id,
                    "sender_type": "user", 
                    "message_text": item.get('query'),
                    "timestamp": item.get('created_at')
                })
                # Pesan balasan dari bot
                cleaned_answer = item.get('answer', '').replace('<trigger_agent>', '').strip()
                if cleaned_answer:
                    history_messages.append({
                        "id": f"dify-bot-{item.get('created_at').isoformat()}",
                        "session_id": session_id,
                        "sender_id": None, # Bot tidak punya ID di tabel users
                        "sender_type": "bot", 
                        "message_text": cleaned_answer,
                        "timestamp": item.get('created_at')
                    })
        
        # 4. Ambil pesan live chat dari DB lokal
        live_messages = session_data.get('messages', [])
        
        # 5. Gabungkan kedua daftar pesan dan urutkan berdasarkan timestamp
        all_messages = history_messages + live_messages
        all_messages.sort(key=lambda x: x['timestamp'])

        # 6. Siapkan data respons final
        response_data = session_data
        # Ganti 'messages' dengan gabungan semua pesan yang sudah urut
        response_data['messages'] = all_messages
        # Kosongkan 'history' karena sudah tidak relevan, semua sudah ada di 'messages'
        response_data['history'] = [] 
        
        return response_data
    
   
    def get_my_active_session(self, agent_id: UUID):
        """Handler untuk agen mengambil sesi aktif yang sedang ditanganinya."""
        active_session = self.repo.get_agent_active_session_by_id(agent_id)
        
        if not active_session:
            return None

        # Gunakan fungsi helper untuk mendapatkan semua detail
        return self._get_full_session_details(active_session['id'])
    
    # --- FUNGSI BARU UNTUK RIWAYAT CHAT ---
    def get_agent_chat_history(self, agent_id: UUID, limit: int, offset: int):
        """Handler untuk mengambil daftar riwayat chat milik agen."""
        return self.repo.get_session_history_for_agent(agent_id, limit, offset)

    def get_agent_chat_transcript(self, session_id: UUID, agent_id: UUID):
        """Handler untuk mengambil satu transkrip spesifik dan memvalidasi kepemilikan."""
        session = self.repo.get_session_with_messages(session_id) # Kita bisa gunakan ulang fungsi ini
        if not session or str(session.get('agent_id')) != str(agent_id) or session.get('status') != 'resolved':
            raise HTTPException(status_code=404, detail="Riwayat sesi tidak ditemukan atau Anda tidak memiliki akses.")
        return session
    
    def initiate_chat_session(self, user_id: UUID, data: ChatSessionInitiateRequest) -> Dict[str, Any]:
        """Membuat sesi chat di DB dengan status 'chatbot' saat pertama kali berinteraksi."""
        new_session = self.repo.create_chat_session(user_id, data.dify_conversation_id, status='chatbot')
        if not new_session:
            raise HTTPException(status_code=500, detail="Could not create initial chat session.")
        return new_session