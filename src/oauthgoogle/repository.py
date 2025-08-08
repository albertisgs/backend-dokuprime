import os
import uuid
import psycopg2
from dotenv import load_dotenv

load_dotenv()

class GoogleAuthRepository:
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

    def get_user_by_email(self, email: str):
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT * FROM user_management WHERE email = %s",
                (email,)
            )
            result = cur.fetchone()
            return result
        finally:
            cur.close()
            conn.close()

    def get_role_id_by_name(self, role_name: str):
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT id FROM role WHERE name = %s LIMIT 1",
                (role_name,)
            )
            role = cur.fetchone()
            return role[0] if role else None
        finally:
            cur.close()
            conn.close()

   
