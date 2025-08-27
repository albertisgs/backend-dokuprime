# src/utils/sessiondependencies.py (Updated)

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
        password=os.getenv("DB_PASSWORD"), host=os.getenv("DB_URL"), port=os.getenv("DB_PORT")
    )
    cur = conn.cursor()
    try:
        # --- QUERY BARU YANG LEBIH POWERFUL ---
        # Query ini mengambil semua data user, tim, dan MENGAGREGASI
        # semua permission dari role user menjadi satu array/list.
        cur.execute(
            """
            SELECT
                u.id, u.username, u.email, u.photo_url,
                um.account_type,
                um.id_team,
                um.id_role,
                t.name as team_name,
                t.access as access, -- Modul yang bisa diakses tim
                r.name as role_name,
                -- Menggunakan ARRAY_AGG untuk mengumpulkan semua permission dari role
                ARRAY_AGG(p.name) FILTER (WHERE p.name IS NOT NULL) as permissions
            FROM sessions s
            JOIN users u ON s.user_id::uuid = u.id
            LEFT JOIN user_management um ON u.id = um.id_user::uuid
            LEFT JOIN teams t ON um.id_team = t.id
            LEFT JOIN roles r ON um.id_role = r.id
            LEFT JOIN role_permissions rp ON r.id = rp.role_id
            LEFT JOIN permissions p ON rp.permission_id = p.id
            WHERE s.session_id = %s AND s.expires_at > %s
            GROUP BY u.id, um.account_type, um.id_team, um.id_role, t.name, t.access, r.name
            """,
            (session_id, datetime.utcnow())
        )
        user_record = cur.fetchone()

        if not user_record:
            raise HTTPException(status_code=401, detail="Invalid or expired session")

        columns = [desc[0] for desc in cur.description]
        user_profile = dict(zip(columns, user_record))

        # Konversi JSON dari kolom 'access' di tabel tim (sekarang jadi access)
        team_modules_list = []
        if user_profile.get('access') and isinstance(user_profile['access'], str):
            team_modules_list = json.loads(user_profile['access'])
            user_profile['access_list'] = team_modules_list
        del user_profile['access']

        # 'permissions' sudah dalam bentuk list dari query ARRAY_AGG
        # Jika user tidak memiliki role/permission, pastikan nilainya adalah list kosong
        if user_profile.get('permissions') is None:
            user_profile['permissions'] = []
        return user_profile
    finally:
        cur.close()
        conn.close()
