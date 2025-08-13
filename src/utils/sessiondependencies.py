from fastapi import Depends, HTTPException, status, Request
import psycopg2
import os
from datetime import datetime

# This dependency should be placed in a central location like `src/utils/dependencies.py`
async def get_current_user_profile(request: Request) -> dict:
    """
    Reads session_id from cookie, validates it, and returns the full user profile.
    This is the primary dependency for protecting routes.
    """
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    

    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host="localhost",
        port=os.getenv("DB_PORT")
    )
    cur = conn.cursor()
    try:
        # Join sessions, users, and user_management to get all data in one query
        cur.execute(
            """
            SELECT
                u.id,
                u.username,
                u.email,
                u.photo_url,
                um.id_role,
                um.account_type
            FROM sessions s
            JOIN users u ON s.user_id::uuid = u.id
            JOIN user_management um ON u.id::text = um.id_user
            WHERE s.session_id = %s AND s.expires_at > %s
            """,
            (session_id, datetime.utcnow())
        )
        user_record = cur.fetchone()

        if not user_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session"
            )
        
        columns = [desc[0] for desc in cur.description]
        return dict(zip(columns, user_record))

    finally:
        cur.close()
        conn.close()


