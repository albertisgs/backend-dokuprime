import os
from dotenv import load_dotenv
import psycopg2
from passlib.context import CryptContext
from typing import Optional
from datetime import datetime, timedelta
import secrets 

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthRepository:
    def __init__(self):
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.db_name = os.getenv("DB_NAME")
        self.port = os.getenv("DB_PORT")
    
    def _get_connection(self):
        return psycopg2.connect(
            dbname=self.db_name,
            user=self.user,
            password=self.password,
            host="localhost",
            port=self.port
        )
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)
    
    async def get_user_by_email(self, email: str) -> Optional[dict]:
        """Fetches a user from the 'users' table by email."""
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            # Simplified query to get core user details first
            cur.execute(
                "SELECT id, username, email, password FROM users WHERE email = %s",
                (email,)
            )
            user = cur.fetchone()
            if user:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, user))
            return None
        finally:
            cur.close()
            conn.close()

    async def create_user(self, user_data: dict) -> dict:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            hashed_password = self.get_password_hash(user_data["password"])
            
            # Insert into users table
            cur.execute(
                """
                INSERT INTO users (username, email, password)
                VALUES (%s, %s, %s)
                RETURNING id, username, email
                """,
                (user_data["username"], user_data["email"], hashed_password)
            )
            new_user = cur.fetchone()
            user_id, username, email = new_user

            # Get default team 'finance'
            cur.execute("SELECT id FROM teams WHERE name = 'finance' LIMIT 1")
            team_row = cur.fetchone()
            if not team_row:
                raise Exception("Default team 'finance' not found")
            team_id = team_row[0]

            # Insert into user_management table
            account_type = 'credential'
            cur.execute(
                """
                INSERT INTO user_management (id_user, id_team, email, account_type)
                VALUES (%s, %s, %s, %s)
                """,
                (str(user_id), str(team_id), email, account_type)
            )
            conn.commit()

            return {
                "id": str(user_id),
                "username": username,
                "email": email,
                # --- CHANGE HERE ---
                "id_team": str(team_id),
                "account_type": account_type
            }
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()

    async def create_session(self, user_id: str, expires_delta_days: int = 7) -> str:
        """Creates a secure session entry in the database."""
        session_id = secrets.token_hex(32)
        expires_at = datetime.now() + timedelta(days=expires_delta_days)
        
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO sessions (session_id, user_id, expires_at)
                VALUES (%s, %s, %s)
                """,
                (session_id, user_id, expires_at)
            )
            conn.commit()
            return session_id
        except Exception as e:
            conn.rollback()
            print(f"Error creating session: {e}") # For logging
            return None
        finally:
            cur.close()
            conn.close()
            
    async def delete_session(self, session_id: str):
        """Deletes a session from the database."""
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM sessions WHERE session_id = %s", (session_id,))
            conn.commit()
        finally:
            cur.close()
            conn.close()