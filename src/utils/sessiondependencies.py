from fastapi import Depends, HTTPException, status, Request
import psycopg2
import os
import json
from datetime import datetime

def get_current_user_profile(request: Request) -> dict:
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"), host="localhost", port=os.getenv("DB_PORT")
    )
    cur = conn.cursor()
    try:
        # Query diperbarui untuk mengambil 'access' dari tabel role
        cur.execute(
            """
            SELECT
                u.id, u.username, u.email, u.photo_url,
                um.id_role, um.account_type,
                r.name as role_name, r.access
            FROM sessions s
            JOIN users u ON s.user_id::uuid = u.id
            LEFT JOIN user_management um ON u.id = um.id_user::uuid
            LEFT JOIN role r ON um.id_role = r.id
            WHERE s.session_id = %s AND s.expires_at > %s
            """,
            (session_id, datetime.utcnow())
        )
        user_record = cur.fetchone()

        if not user_record:
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        
        columns = [desc[0] for desc in cur.description]
        user_profile = dict(zip(columns, user_record))

        # Proses daftar hak akses
        access_list = []
        if user_profile.get('access') and isinstance(user_profile['access'], str):
            access_list = json.loads(user_profile['access'])
        
        # PERUBAHAN: Logika dashboard wajib dihapus
        user_profile['access_list'] = access_list
        del user_profile['access'] # Hapus kolom 'access' mentah

        return user_profile
    finally:
        cur.close()
        conn.close()