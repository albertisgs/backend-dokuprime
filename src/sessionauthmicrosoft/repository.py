import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime, timedelta
import secrets
from .schemas import UserInfo # Import UserInfo for type hinting

load_dotenv()

class MicrosoftAuthRepository:
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

    async def find_or_create_user(self, user_info: UserInfo) -> dict | None:
        """
        Finds a user by email. If they don't exist, creates them in both
        the `users` and `user_management` tables with a default 'finance' team.
        """
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            # 1. Check if a user with this email already exists in the `users` table.
            cur.execute("SELECT id, username, email FROM users WHERE email = %s", (user_info.email,))
            user_record = cur.fetchone()

            if not user_record:
                # User is completely new. Create in `users` and `user_management`.
                unusable_password = secrets.token_hex(32) # Secure, unused password
                cur.execute(
                    "INSERT INTO users (username, email, password) VALUES (%s, %s, %s) RETURNING id, username, email",
                    (user_info.name, user_info.email, unusable_password)
                )
                user_record = cur.fetchone()
                new_user_id = user_record[0]

                # Check if a user_management entry already exists (unlikely, but safe)
                cur.execute("SELECT id FROM user_management WHERE email = %s", (user_info.email,))
                if not cur.fetchone():
                    # Get default team 'finance'
                    cur.execute("SELECT id FROM teams WHERE name = 'finance' LIMIT 1")
                    team_row = cur.fetchone()
                    if not team_row:
                        raise Exception("Default team 'finance' not found")
                    team_id = team_row[0]

                    # Create entry in `user_management`
                    cur.execute(
                        "INSERT INTO user_management (id_user, id_team, email, account_type) VALUES (%s, %s, %s, %s)",
                        (str(new_user_id), str(team_id), user_info.email, 'microsoft')
                    )
                conn.commit()

            # At this point, user_record is guaranteed to be populated.
            columns = ['id', 'username', 'email']
            return dict(zip(columns, user_record))

        except Exception as e:
            conn.rollback()
            print(f"Database error in find_or_create_user: {e}")
            raise e
        finally:
            cur.close()
            conn.close()

    async def create_session(self, user_id: str) -> str | None:
        """Creates a secure session entry in the database."""
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