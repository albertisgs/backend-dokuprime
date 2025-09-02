# src/live_chat/repository.py

import os
import psycopg2
from uuid import UUID
from typing import List, Optional
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

    def create_chat_session(self, user_id: UUID, dify_conversation_id: UUID) -> dict:
        """Membuat sesi chat baru dengan status 'pending'."""
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            sql = """
                INSERT INTO live_chat_sessions (user_id, dify_conversation_id, status)
                VALUES (%s, %s, 'pending')
                RETURNING id, user_id, status, created_at;
            """
            cur.execute(sql, (str(user_id), str(dify_conversation_id)))
            new_session = self._map_row_to_dict(cur.fetchone(), cur)
            conn.commit()
            return new_session
        finally:
            cur.close()
            conn.close()

    def get_dify_history(self, conversation_id: UUID) -> List[dict]:
        """Mengambil riwayat percakapan dari database Dify (READ-ONLY)."""
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
        """Mengambil semua sesi yang 'pending' untuk ditampilkan di antrian."""
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
                WHERE lcs.status = 'pending'
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
        """Mengubah status sesi menjadi 'active' dan menetapkan agent_id."""
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            sql = """
                UPDATE live_chat_sessions
                SET status = 'active', agent_id = %s, claimed_at = CURRENT_TIMESTAMP
                WHERE id = %s AND status = 'pending'
                RETURNING *;
            """
            cur.execute(sql, (str(agent_id), str(session_id)))
            updated_session = self._map_row_to_dict(cur.fetchone(), cur)
            conn.commit()
            return updated_session
        finally:
            cur.close()
            conn.close()

    def add_message(self, session_id: UUID, sender_id: UUID, sender_type: str, text: str) -> dict:
        """Menambahkan pesan baru ke sesi live chat."""
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
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            # Get session details
            cur.execute("SELECT * FROM live_chat_sessions WHERE id = %s", (str(session_id),))
            session_data = self._map_row_to_dict(cur.fetchone(), cur)
            if not session_data:
                return None

            # Get messages for the session
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
    
    def end_session(self, session_id: UUID, agent_id: UUID) -> Optional[dict]:
        """Mengubah status sesi menjadi 'closed'."""
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            sql = """
                UPDATE live_chat_sessions
                SET status = 'closed', ended_at = CURRENT_TIMESTAMP
                WHERE id = %s AND agent_id = %s AND status = 'active'
                RETURNING *;
            """
            cur.execute(sql, (str(session_id), str(agent_id)))
            closed_session = self._map_row_to_dict(cur.fetchone(), cur)
            conn.commit()
            return closed_session
        finally:
            cur.close()
            conn.close()

