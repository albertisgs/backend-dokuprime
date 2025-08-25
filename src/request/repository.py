# src/request/repository.py

import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

class RequestRepository:
    def __init__(self):
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.db_name = os.getenv("DB_NAME")
        self.port = os.getenv("DB_PORT")
        print("Request Repository Initialized!")

    def _get_connection(self):
        """Membuat dan mengembalikan koneksi database baru."""
        return psycopg2.connect(
            dbname=self.db_name,
            user=self.user,
            password=self.password,
            host="localhost",
            port=self.port
        )

    async def addPromptRepo(
            self,
            usecase_name: str,
            priority: str,
            user_request: str,
            team: str,
            reason: str,
            prompt: str
        ):
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                # Menggunakan parameterized query untuk keamanan
                sql = """
                    INSERT INTO user_requests 
                    (usecase_name, priority, user_request, team, reason, prompt)
                    VALUES (%s, %s, %s, %s, %s, %s);
                """
                cursor.execute(sql, (usecase_name, priority, user_request, team, reason, prompt))
                conn.commit()
        finally:
            conn.close()
        print("New prompt successfully added")

    async def getRequestRepo(self, team_name: str = None):
        print("Fetching requests from database...")
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                sql = "SELECT * FROM user_requests"
                params = []
                
                if team_name:
                    sql += " WHERE team = %s"
                    params.append(team_name)
                    
                sql += " ORDER BY request_date DESC"
                cur.execute(sql, tuple(params))
                
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                data = [dict(zip(columns, row)) for row in rows]
                return data
        finally:
            conn.close()

    async def getRequestByIdRepo(self, id: int):
        print(f"Fetching request by id {id}...")
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                sql = "SELECT * FROM user_requests WHERE id = %s"
                cur.execute(sql, (id,))
                row = cur.fetchone()
                if row:
                    colnames = [desc[0] for desc in cur.description]
                    return dict(zip(colnames, row))
                return None
        finally:
            conn.close()

    async def updatePromptRepo(self, id: int, data: dict):
        print(f"Updating prompt with id {id}...")
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                fields = [f"{key} = %s" for key in data.keys()]
                values = list(data.values())
                values.append(id)
                
                sql = f"UPDATE user_requests SET {', '.join(fields)} WHERE id = %s RETURNING *;"
                cur.execute(sql, tuple(values))
                
                updated_row = cur.fetchone()
                conn.commit()
                
                if updated_row:
                    colnames = [desc[0] for desc in cur.description]
                    return dict(zip(colnames, updated_row))
                return None
        finally:
            conn.close()

    async def deletePromptRepo(self, id: int):
        print(f"Deleting prompt with id {id}...")
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM user_requests WHERE id = %s;", (id,))
                conn.commit()
                return cur.rowcount > 0
        finally:
            conn.close()

    async def updateStatusRepo(self, id: int, status: str):
        print(f"Updating status for prompt id {id} to {status}...")
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                sql = "UPDATE user_requests SET status = %s WHERE id = %s RETURNING *;"
                cur.execute(sql, (status, id))
                updated_row = cur.fetchone()
                conn.commit()
                
                if updated_row:
                    colnames = [desc[0] for desc in cur.description]
                    return dict(zip(colnames, updated_row))
                return None
        finally:
            conn.close()