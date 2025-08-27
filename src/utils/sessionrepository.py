
import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime, timedelta
import secrets
from typing import Optional

load_dotenv()

class SessionRepository:
    """
    This class handles all database operations related to the 'sessions' table.
    It provides a centralized way to manage user sessions.
    """
    def __init__(self):
        """Initializes database connection parameters from environment variables."""
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.db_name = os.getenv("DB_NAME")
        self.port = os.getenv("DB_PORT")
        self.host = os.getenv("DB_URL")

    def _get_connection(self):
        """Establishes and returns a new database connection."""
        return psycopg2.connect(
            dbname=self.db_name, user=self.user, password=self.password,
            host=self.host, port=self.port
        )

    def create_session(self, user_id: str) -> Optional[str]:
        """
        Creates a new, secure session for a given user_id.

        Args:
            user_id: The UUID of the user to create a session for.

        Returns:
            The generated session_id string if successful, otherwise None.
        """
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

    def get_session_data(self, session_id: str) -> Optional[dict]:
        """
        Retrieves session data for a given session_id if it's valid and not expired.

        Args:
            session_id: The session ID from the user's cookie.

        Returns:
            A dictionary containing the session data (e.g., user_id) if valid, otherwise None.
        """
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT user_id FROM sessions WHERE session_id = %s AND expires_at > %s",
                (session_id, datetime.utcnow())
            )
            record = cur.fetchone()
            if record:
                return {"user_id": record[0]}
            return None
        finally:
            cur.close()
            conn.close()

    def delete_session(self, session_id: str) -> bool:
        """
        Deletes a session from the database, effectively logging the user out.

        Args:
            session_id: The session ID to delete.

        Returns:
            True if a session was deleted, False otherwise.
        """
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM sessions WHERE session_id = %s", (session_id,))
            conn.commit()
            # cur.rowcount will be 1 if a row was deleted, 0 otherwise.
            return cur.rowcount > 0
        except Exception as e:
            print(f"Database error deleting session: {e}")
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

    def get_by_user_id(self, user_id: str) -> Optional[dict]:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM user_management WHERE id_user = %s", (user_id,))
            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
            return None
        finally:
            cur.close()
            conn.close()
