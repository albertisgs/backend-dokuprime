# src/notifications/repository.py
import os
import psycopg2
from uuid import UUID
from typing import List
from psycopg2.extras import execute_values

class NotificationRepository:
    def __init__(self):
        # ... (Inisialisasi koneksi DB seperti repository lainnya) ...
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.db_name = os.getenv("DB_NAME")
        self.port = os.getenv("DB_PORT")
        self.host = os.getenv("DB_URL")

    def _get_connection(self):
        return psycopg2.connect(
            dbname=self.db_name, user=self.user, password=self.password,
            host=self.host, port=self.port
        )

    def create_notification(self, data: dict, creator_id: UUID, creator_type: str) -> dict:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            # Dapatkan nilai target_id dan ubah ke string jika ada
            target_id = data.get('target_id')
            if target_id:
                target_id = str(target_id)
            
            # Ubah creator_id ke string jika ada
            if creator_id:
                creator_id = str(creator_id)

            cur.execute(
                """
                INSERT INTO notifications (title, message, target_type, target_id, creator_id, creator_type, link_to)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id, created_at
                """,
                # Gunakan variabel yang sudah dikonversi
                (data['title'], data['message'], data['target_type'], target_id, creator_id, creator_type, data.get('link_to'))
            )
            new_notif = cur.fetchone()
            conn.commit()
            return {"id": new_notif[0], "created_at": new_notif[1]}
        finally:
            cur.close()
            conn.close()

    def get_target_users(self, target_type: str, target_id: UUID = None) -> List[dict]:
        """Mengambil daftar pengguna target (ID dan email)."""
        conn = self._get_connection()
        cur = conn.cursor()
        query = ""
        params = ()
        
        target_id_str = str(target_id) if target_id else None

        if target_type == 'all':
            query = "SELECT id, email FROM users;"
        elif target_type == 'team' and target_id_str:
            # Mengambil email langsung dari user_management
            query = "SELECT id_user::uuid as id, email FROM user_management WHERE id_team = %s;"
            params = (target_id_str,)
        elif target_type == 'user' and target_id_str:
            query = "SELECT id, email FROM users WHERE id = %s;"
            params = (target_id_str,)
        
        if not query:
            cur.close()
            conn.close()
            return []

        cur.execute(query, params)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        users = [dict(zip(columns, row)) for row in rows]
        
        cur.close()
        conn.close()
        return users


    def get_target_user_ids(self, target_type: str, target_id: UUID = None) -> List[UUID]:
        conn = self._get_connection()
        cur = conn.cursor()
        query = ""
        params = ()
        
        # Konversi target_id ke string jika ada
        if target_id:
            target_id_str = str(target_id)
        else:
            target_id_str = None

        if target_type == 'all':
            query = "SELECT id FROM users;"
        elif target_type == 'team' and target_id_str:
            query = "SELECT id_user::uuid FROM user_management WHERE id_team = %s;"
            params = (target_id_str,)
        elif target_type == 'user' and target_id_str:
            query = "SELECT id FROM users WHERE id = %s;"
            params = (target_id_str,)
        
        if not query:
            return []

        cur.execute(query, params)
        user_ids = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        return user_ids

    def link_notification_to_users(self, notif_id: UUID, user_ids: List[UUID]):
        if not user_ids:
            return
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            # Menggunakan execute_values untuk efisiensi bulk insert
            args_list = [(user_id, notif_id) for user_id in user_ids]
            execute_values(
                cur,
                "INSERT INTO user_notifications (user_id, notification_id) VALUES %s",
                args_list
            )
            conn.commit()
        finally:
            cur.close()
            conn.close()
            
    def get_notifications_for_user(self, user_id: UUID, limit: int = 10, offset: int = 0):
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT
                    un.id, n.id as notification_id, n.title, n.message, n.created_at, un.is_read, n.link_to
                FROM user_notifications un
                JOIN notifications n ON un.notification_id = n.id
                WHERE un.user_id = %s
                ORDER BY n.created_at DESC
                LIMIT %s OFFSET %s;
                """,
                (user_id, limit, offset)
            )
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            notifications = [dict(zip(columns, row)) for row in rows]
            
            # Hanya hitung unread_count jika ini adalah halaman pertama (offset = 0)
            unread_count = 0
            if offset == 0:
                cur.execute("SELECT COUNT(*) FROM user_notifications WHERE user_id = %s AND is_read = FALSE;", (user_id,))
                unread_count = cur.fetchone()[0]
            
            return {"unread_count": unread_count, "notifications": notifications}
        finally:
            cur.close()
            conn.close()

    def mark_all_as_read(self, user_id: UUID) -> bool:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "UPDATE user_notifications SET is_read = TRUE, read_at = CURRENT_TIMESTAMP WHERE user_id = %s AND is_read = FALSE",
                (user_id,)
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            cur.close()
            conn.close()

    # Tambahkan fungsi ini di dalam kelas NotificationRepository
    def mark_as_read(self, user_id: UUID, notification_id: UUID) -> bool:
        """Menandai satu notifikasi spesifik sebagai telah dibaca untuk seorang pengguna."""
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                UPDATE user_notifications SET is_read = TRUE, read_at = CURRENT_TIMESTAMP
                WHERE user_id = %s AND id = %s
                """,
                (str(user_id), str(notification_id))
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            cur.close()
            conn.close()

    def delete_user_notification(self, user_id: UUID, user_notification_id: UUID) -> bool:
        """Menghapus satu entri user_notification spesifik."""
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                DELETE FROM user_notifications
                WHERE user_id = %s AND id = %s
                """,
                (str(user_id), str(user_notification_id))
            )
            conn.commit()
            return cur.rowcount > 0 # Return True jika ada baris yang terhapus
        finally:
            cur.close()
            conn.close()