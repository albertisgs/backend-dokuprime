# src/live_chat/repository.py (Diperbarui)

import os
import psycopg2
from uuid import UUID
from typing import List, Optional, Dict, Any
from datetime import datetime

class LiveChatRepository:
    def __init__(self):
        # Koneksi ke database utama
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.db_name = os.getenv("DB_NAME")
        self.port = os.getenv("DB_PORT")
        self.host = os.getenv("DB_URL")

        # Koneksi ke database Dify (read-only)
        self.dify_user = os.getenv("DIFY_DB_USER")
        self.dify_password = os.getenv("DIFY_DB_PASSWORD")
        self.dify_db_name = os.getenv("DIFY_DB_NAME")
        self.dify_port = os.getenv("DIFY_DB_PORT")
        self.dify_host = os.getenv("DIFY_DB_URL")

    def _get_connection(self):
        """Koneksi ke DB utama Dokuprime."""
        return psycopg2.connect(
            dbname=self.db_name, user=self.user, password=self.password,
            host=self.host, port=self.port
        )

    def _get_dify_connection(self):
        """Koneksi ke DB Dify."""
        return psycopg2.connect(
            dbname=self.dify_db_name, user=self.dify_user, password=self.dify_password,
            host=self.dify_host, port=self.dify_port
        )

    def _map_row_to_dict(self, row, cursor):
        if not row:
            return None
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))

    # --- FUNGSI BARU ---
    def set_agent_status(self, agent_id: UUID, status: str) -> Optional[dict]:
        """Mengatur status agen (online, away, offline) dan memperbarui last_seen_at."""
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            # Jika agen offline, pastikan mereka tidak menangani sesi apa pun
            current_session_id_update = ", current_session_id = NULL" if status == 'offline' else ""
            
            sql = f"""
                UPDATE users
                SET agent_status = %s, last_seen_at = NOW() {current_session_id_update}
                WHERE id = %s
                RETURNING id, username, agent_status;
            """
            cur.execute(sql, (status, str(agent_id)))
            updated_agent = self._map_row_to_dict(cur.fetchone(), cur)
            conn.commit()
            return updated_agent
        finally:
            cur.close()
            conn.close()

    # --- FUNGSI BARU ---
    def find_available_agent(self) -> Optional[Dict[str, Any]]:
        """Mencari agen yang 'online' dan tidak sedang dalam sesi."""
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            # Cari agen yang online dan tidak memiliki current_session_id
            sql = """
                SELECT id, username FROM users
                WHERE agent_status = 'online' AND current_session_id IS NULL
                ORDER BY last_seen_at ASC -- Ambil yang paling lama tidak aktif
                LIMIT 1;
            """
            cur.execute(sql)
            return self._map_row_to_dict(cur.fetchone(), cur)
        finally:
            cur.close()
            conn.close()

    def create_chat_session(self, user_id: UUID, dify_conversation_id: UUID, status: str = 'chatbot') -> dict:
        """Membuat sesi chat baru dengan status awal 'chatbot' atau 'queued'."""
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            # Status default adalah 'chatbot', akan menjadi 'queued' jika langsung minta agen
            sql = """
                INSERT INTO live_chat_sessions (user_id, dify_conversation_id, status)
                VALUES (%s, %s, %s)
                RETURNING id, user_id, status, created_at;
            """
            cur.execute(sql, (str(user_id), str(dify_conversation_id), status))
            new_session = self._map_row_to_dict(cur.fetchone(), cur)
            conn.commit()
            return new_session
        finally:
            cur.close()
            conn.close()
            
    # --- FUNGSI BARU ---
    def get_user_active_sessions(self, user_id: UUID) -> List[dict]:
        """Mengambil semua sesi aktif (bukan 'closed' atau 'resolved') untuk seorang user."""
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            sql = """
                SELECT lcs.id, lcs.status, lcs.created_at, u.username as agent_name
                FROM live_chat_sessions lcs
                LEFT JOIN users u ON lcs.agent_id = u.id
                WHERE lcs.user_id = %s AND lcs.status NOT IN ('closed', 'resolved')
                ORDER BY lcs.created_at DESC;
            """
            cur.execute(sql, (str(user_id),))
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in rows]
        finally:
            cur.close()
            conn.close()

    def get_dify_history(self, conversation_id: UUID) -> List[dict]:
        """Mengambil riwayat percakapan dari database Dify (READ-ONLY)."""
        # (Fungsi ini tidak berubah)
        conn = self._get_dify_connection()
        cur = conn.cursor()
        try:
            sql = """
                SELECT query, answer, created_at
                FROM public.messages
                WHERE conversation_id = %s
                ORDER BY created_at ASC;
            """
            cur.execute(sql, (str(conversation_id),))
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in rows]
        finally:
            cur.close()
            conn.close()

    def get_pending_sessions_for_queue(self) -> List[dict]:
        """Mengambil semua sesi yang 'queued' untuk ditampilkan di antrian."""
        # (Logika query sedikit berubah untuk mencocokkan status 'queued')
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            sql = """
                SELECT 
                    lcs.id as session_id,
                    u.username as user_name,
                    lcs.created_at,
                    lcs.status
                FROM live_chat_sessions lcs
                JOIN users u ON lcs.user_id = u.id
                WHERE lcs.status = 'queued'
                ORDER BY lcs.created_at ASC;
            """
            cur.execute(sql)
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in rows]
        finally:
            cur.close()
            conn.close()

    def claim_session(self, session_id: UUID, agent_id: UUID) -> Optional[dict]:
        """
        Mengubah status sesi menjadi 'active', menetapkan agent_id,
        DAN mengunci agen ke sesi ini.
        (DIPERBARUI): Sekarang melakukan JOIN untuk mengembalikan user_name.
        """
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            # Langkah 1: Lakukan UPDATE seperti biasa, tapi jangan RETURNING dulu
            sql_update_session = """
                UPDATE live_chat_sessions
                SET status = 'active', agent_id = %s, claimed_at = CURRENT_TIMESTAMP
                WHERE id = %s AND status = 'queued';
            """
            cur.execute(sql_update_session, (str(agent_id), str(session_id)))

            # Periksa apakah ada baris yang terpengaruh. Jika tidak, sesi sudah diklaim orang lain.
            if cur.rowcount == 0:
                conn.rollback()
                return None

            # Langkah 2: Kunci agen ke sesi ini
            sql_update_agent = """
                UPDATE users
                SET current_session_id = %s
                WHERE id = %s;
            """
            cur.execute(sql_update_agent, (str(session_id), str(agent_id)))
            
            # Langkah 3: SEKARANG, ambil data sesi yang sudah diupdate dengan JOIN
            sql_select_updated = """
                SELECT lcs.*, u.username as user_name
                FROM live_chat_sessions lcs
                JOIN users u ON lcs.user_id = u.id
                WHERE lcs.id = %s;
            """
            cur.execute(sql_select_updated, (str(session_id),))
            updated_session_with_name = self._map_row_to_dict(cur.fetchone(), cur)

            conn.commit()
            return updated_session_with_name
        finally:
            cur.close()
            conn.close()
            
    # --- FUNGSI BARU ---
    def transfer_session(self, session_id: UUID, from_agent_id: UUID, to_agent_id: UUID) -> Optional[dict]:
        """Memindahkan sesi dari satu agen ke agen lain."""
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            # 1. Update sesi dengan agent_id baru dan catat siapa yang mentransfer
            sql_session = """
                UPDATE live_chat_sessions
                SET agent_id = %s, transferred_by_agent_id = %s, status = 'active'
                WHERE id = %s AND agent_id = %s
                RETURNING *;
            """
            cur.execute(sql_session, (str(to_agent_id), str(from_agent_id), str(session_id), str(from_agent_id)))
            updated_session = self._map_row_to_dict(cur.fetchone(), cur)

            if not updated_session:
                conn.rollback()
                return None
            
            # 2. Lepaskan sesi dari agen lama
            cur.execute("UPDATE users SET current_session_id = NULL WHERE id = %s", (str(from_agent_id),))

            # 3. Kunci sesi ke agen baru
            cur.execute("UPDATE users SET current_session_id = %s WHERE id = %s", (str(session_id), str(to_agent_id)))
            
            conn.commit()
            return updated_session
        finally:
            cur.close()
            conn.close()


    def add_message(self, session_id: UUID, sender_id: UUID, sender_type: str, text: str) -> dict:
        """Menambahkan pesan baru ke sesi live chat."""
        # (Fungsi ini tidak berubah)
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            sql = """
                INSERT INTO live_chat_messages (session_id, sender_id, sender_type, message_text)
                VALUES (%s, %s, %s, %s)
                RETURNING *;
            """
            cur.execute(sql, (str(session_id), str(sender_id), sender_type, text))
            new_message = self._map_row_to_dict(cur.fetchone(), cur)
            conn.commit()
            return new_message
        finally:
            cur.close()
            conn.close()

    def get_session_with_messages(self, session_id: UUID) -> Optional[dict]:
        """Mengambil detail sesi beserta semua pesannya."""
        # (Fungsi ini tidak berubah)
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM live_chat_sessions WHERE id = %s", (str(session_id),))
            session_data = self._map_row_to_dict(cur.fetchone(), cur)
            if not session_data:
                return None

            sql_messages = """
                SELECT * FROM live_chat_messages 
                WHERE session_id = %s 
                ORDER BY "timestamp" ASC;
            """
            cur.execute(sql_messages, (str(session_id),))
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            session_data['messages'] = [dict(zip(columns, row)) for row in rows]
            
            return session_data
        finally:
            cur.close()
            conn.close()
    
    def end_session(self, session_id: UUID, agent_id: UUID, final_transcript: str) -> Optional[dict]:
        """Mengubah status sesi menjadi 'resolved' dan melepaskan agen dari sesi."""
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            # 1. Update sesi menjadi resolved dan simpan transkrip
            sql_session = """
                UPDATE live_chat_sessions
                SET status = 'resolved', ended_at = CURRENT_TIMESTAMP, transcript = %s
                WHERE id = %s AND agent_id = %s AND status = 'active'
                RETURNING *;
            """
            cur.execute(sql_session, (final_transcript, str(session_id), str(agent_id)))
            closed_session = self._map_row_to_dict(cur.fetchone(), cur)

            if not closed_session:
                conn.rollback()
                return None

            # 2. Lepaskan agen dari sesi ini agar bisa menerima chat baru
            cur.execute("UPDATE users SET current_session_id = NULL WHERE id = %s", (str(agent_id),))

            conn.commit()
            return closed_session
        finally:
            cur.close()
            conn.close()

    # --- FUNGSI BARU ---
    def get_canned_responses_for_team(self, team_id: UUID) -> List[dict]:
        """Mengambil semua pesan cepat untuk sebuah tim."""
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            sql = """
                SELECT id, shortcut, message_text FROM canned_responses
                WHERE team_id = %s ORDER BY shortcut;
            """
            cur.execute(sql, (str(team_id),))
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in rows]
        finally:
            cur.close()
            conn.close()
    
    
    def get_session_history_for_user(self, session_id: UUID, user_id: UUID) -> Optional[dict]:
        """
        Mengambil detail sesi beserta semua pesannya, HANYA jika session_id tersebut
        milik user_id yang diberikan. Ini mencegah user melihat sesi orang lain.
        """
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            # Ambil detail sesi dan validasi kepemilikan dalam satu query
            sql = """
                SELECT * FROM live_chat_sessions 
                WHERE id = %s AND user_id = %s;
            """
            cur.execute(sql, (str(session_id), str(user_id)))
            session_data = self._map_row_to_dict(cur.fetchone(), cur)
            
            # Jika tidak ada hasil, berarti sesi tidak ada atau bukan milik user ini
            if not session_data:
                return None

            # Ambil pesan untuk sesi tersebut jika validasi berhasil
            sql_messages = """
                SELECT * FROM live_chat_messages 
                WHERE session_id = %s 
                ORDER BY "timestamp" ASC;
            """
            cur.execute(sql_messages, (str(session_id),))
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            session_data['messages'] = [dict(zip(columns, row)) for row in rows]
            
            return session_data
        finally:
            cur.close()
            conn.close()
            
    def get_agent_active_session_by_id(self, agent_id: UUID) -> Optional[dict]:
        """
        Mengambil sesi chat yang sedang aktif ditangani oleh seorang agen.
        """
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            # Query ini mengambil data sesi dengan join ke tabel user untuk mendapatkan nama user
            sql = """
                SELECT
                    lcs.*,
                    u.username as user_name
                FROM live_chat_sessions lcs
                JOIN users u ON lcs.user_id = u.id
                WHERE lcs.agent_id = %s AND lcs.status = 'active'
                LIMIT 1;
            """
            cur.execute(sql, (str(agent_id),))
            session_data = self._map_row_to_dict(cur.fetchone(), cur)
            
            return session_data
        finally:
            cur.close()
            conn.close()