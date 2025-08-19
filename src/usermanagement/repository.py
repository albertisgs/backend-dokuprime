import os
import uuid
import psycopg2
from dotenv import load_dotenv
from typing import List, Optional
from .schemas import UserManagementCreate, UserManagementUpdate

load_dotenv()

class UserManagementRepository:
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

    def list_all(self) -> List[dict]:
        """
        PERBAIKAN: Mengambil semua data pengguna dan langsung menyertakan
        nama team dengan satu query JOIN yang efisien.
        """
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                 SELECT
                    um.id,
                    um.id_user,
                    um.id_team,
                    um.id_role,  -- Tambahkan
                    um.email,
                    um.account_type,
                    t.name AS team_name,
                    r.name AS role_name -- Tambahkan
                FROM user_management um
                LEFT JOIN teams t ON um.id_team = t.id
                LEFT JOIN roles r ON um.id_role = r.id -- Tambahkan JOIN
                ORDER BY um.email;
                """
            )
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in rows]
        finally:
            cur.close()
            conn.close()

    def get_by_id(self, id: str) -> Optional[dict]:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM user_management WHERE id = %s", (id,))
            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
            return None
        finally:
            cur.close()
            conn.close()

    def create(self, data: UserManagementCreate) -> dict:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            new_id = str(uuid.uuid4())
            cur.execute(
                """
                INSERT INTO user_management (id, id_team, id_role, email, account_type)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, id_team, id_role, email, account_type
                """,
                (new_id, data.id_team, data.id_role, data.email, data.account_type)
            )
            row = cur.fetchone()
            columns = [desc[0] for desc in cur.description]
            conn.commit()
            return dict(zip(columns, row))
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()

    def update(self, id: str, data: UserManagementUpdate) -> Optional[dict]:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            fields = []
            values = []

            # Add this block to handle the id_user field
            if data.id_user is not None:
                fields.append("id_user = %s")
                values.append(data.id_user)
            
            if data.id_team:
                fields.append("id_team = %s")
                values.append(data.id_team)

            if data.id_role is not None:
                fields.append("id_role = %s")
                values.append(data.id_role)
                
            if data.account_type:
                fields.append("account_type = %s")
                values.append(data.account_type)

            if not fields:
                return None  # nothing to update

            values.append(id)
            query = f"UPDATE user_management SET {', '.join(fields)} WHERE id = %s RETURNING *"
            cur.execute(query, tuple(values))
            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                conn.commit()
                return dict(zip(columns, row))
            return None
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()

    def delete(self, id: str) -> bool:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM user_management WHERE id = %s", (id,))
            conn.commit()
            return cur.rowcount > 0
        finally:
            cur.close()
            conn.close()


    def check(self, email: str) -> Optional[dict]:

            conn = self._get_connection()
            cur = conn.cursor()
            try:
                cur.execute("SELECT * FROM user_management WHERE email = %s", (email,))
                row = cur.fetchone()
                if row:
                    columns = [desc[0] for desc in cur.description]
                    return dict(zip(columns, row))
                return None
            finally:
                cur.close()
                conn.close()

    def get_team_id_by_name(self, team_name: str):
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT id FROM teams WHERE name = %s LIMIT 1",
                (team_name,)
            )
            team = cur.fetchone()
            return team[0] if team else None
        finally:
            cur.close()
            conn.close()

    def list_teams(self) -> List[dict]:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            # Select only the columns needed for the teamOut schema
            cur.execute("SELECT id, name FROM teams")
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in rows]
        finally:
            cur.close()
            conn.close()

    def get_team_by_id(self, team_id: str) -> Optional[dict]:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT name FROM teams WHERE id = %s", (team_id,))
            row = cur.fetchone()
            if row:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
            return None
        finally:
            cur.close()
            conn.close()