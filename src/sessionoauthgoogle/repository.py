# ======================================================================
# src/oauthgoogle/repository.py (LOGIKA DIPERBARUI)
# ======================================================================

import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime, timedelta
import secrets
from .schemas import UserInfo # Import UserInfo for type hinting

load_dotenv()

class GoogleAuthRepository:
    def __init__(self):
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.db_name = os.getenv("DB_NAME")
        self.port = os.getenv("DB_PORT")

    def _get_connection(self):
        return psycopg2.connect(
            dbname=self.db_name, user=self.user, password=self.password,
            host="localhost", port=self.port
        )

    async def process_user_login(self, user_info: UserInfo) -> dict | None:
        """
        Menerapkan logika 7 langkah yang Anda tentukan:
        1. Cek user_management (allowlist).
        2. Jika tidak ada, tolak (unauthorized).
        3. Jika ada, cek tabel users.
        4. Jika user ada, update profilnya.
        5. Jika user tidak ada, buat user baru.
        6. Update id_user di user_management.
        7. Jika semua lengkap, otorisasi.
        """
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            # Langkah 1 & 2: Cek apakah email ada di allowlist user_management
            cur.execute(
                "SELECT id, id_user FROM user_management WHERE email = %s AND account_type = 'google'",
                (user_info.email,)
            )
            management_record = cur.fetchone()

            if not management_record:
                # Pengguna tidak ada di allowlist, akses ditolak.
                return None

            management_id, existing_user_id = management_record

            # Langkah 3: Cek email di tabel users
            cur.execute("SELECT id FROM users WHERE email = %s", (user_info.email,))
            user_record_in_users = cur.fetchone()

            internal_user_id = None
            if user_record_in_users:
                # Langkah 4: Jika user ada, update profilnya
                internal_user_id = user_record_in_users[0]
                cur.execute(
                    """
                    UPDATE users SET username = %s, photo_url = %s
                    WHERE id = %s
                    """,
                    (user_info.name, user_info.picture, internal_user_id)
                )
            else:
                # Langkah 5: Jika user tidak ada, buat user baru
                unusable_password = secrets.token_hex(32)
                cur.execute(
                    """
                    INSERT INTO users (username, email, password, photo_url)
                    VALUES (%s, %s, %s, %s) RETURNING id;
                    """,
                    (user_info.name, user_info.email, unusable_password, user_info.picture)
                )
                new_user_id_record = cur.fetchone()
                internal_user_id = new_user_id_record[0]

            # Langkah 6: Jika id_user di user_management masih kosong, update
            if not existing_user_id:
                cur.execute(
                    "UPDATE user_management SET id_user = %s WHERE id = %s",
                    (str(internal_user_id), management_id)
                )
            
            # Ambil data user yang sudah lengkap untuk membuat sesi
            cur.execute(
                "SELECT id, username, email, photo_url FROM users WHERE id = %s",
                (internal_user_id,)
            )
            final_user_record = cur.fetchone()
            
            conn.commit()

            if final_user_record:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, final_user_record))
            
            return None

        except Exception as e:
            conn.rollback()
            print(f"Database error in process_user_login: {e}")
            raise e
        finally:
            cur.close()
            conn.close()

    async def create_session(self, user_id: str) -> str | None:
        """Membuat sesi aman untuk UUID pengguna yang diberikan."""
        session_id = secrets.token_hex(32)
        expires_at = datetime.utcnow() + timedelta(days=7)
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO sessions (session_id, user_id, expires_at) VALUES (%s, %s, %s)",
                (session_id, user_id, expires_at)
            )
            conn.commit()
            return session_id
        except Exception as e:
            print(f"Database error creating session: {e}")
            conn.rollback()
            return None
        finally:
            cur.close()
            conn.close()