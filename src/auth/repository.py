import os
from dotenv import load_dotenv
import psycopg2
from passlib.context import CryptContext
from typing import Optional

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
    
    async def get_user(self, email: str) -> Optional[dict]:
        conn = self._get_connection()
        cur = conn.cursor()

        try:
            cur.execute(
                """
                SELECT 
                    u.id, u.username, u.email, u.password,
                    um.id_role, um.account_type
                FROM users u
                LEFT JOIN user_management um ON um.id_user = u.id::text
                WHERE u.email = %s
                """,
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
            # 1. Hash the password
            hashed_password = self.get_password_hash(user_data["password"])


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

            cur.execute(
                "SELECT id FROM role WHERE name = 'finance' LIMIT 1"
            )
            role_row = cur.fetchone()
            if not role_row:
                raise Exception("Default role 'finance' not found")
            role_id = role_row[0]

            account_type = 'credential'
            cur.execute(
                """
                INSERT INTO user_management (id_user, id_role, email, account_type)
                VALUES (%s, %s, %s, %s)
                """,
                (str(user_id), str(role_id), email, account_type)
            )

            conn.commit()

     
            return {
                "id": str(user_id),
                "username": username,
                "email": email,
                "id_role": str(role_id),
                "account_type": account_type
            }

        except Exception as e:
            conn.rollback()
            raise e

        finally:
            cur.close()
            conn.close()
