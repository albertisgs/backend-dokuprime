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
            cur.execute(
                """INSERT INTO users (username, email, password)
                VALUES (%s, %s, %s) RETURNING id, username, email""",
                (user_data["username"], user_data["email"], hashed_password)
            )
            new_user = cur.fetchone()
            conn.commit()
            
            columns = [desc[0] for desc in cur.description]
            return dict(zip(columns, new_user))
        finally:
            cur.close()
            conn.close()