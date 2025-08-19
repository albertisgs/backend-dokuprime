import psycopg2
import os
from typing import List, Optional
from uuid import UUID
from .schemas import RoleCreate
from psycopg2.extras import execute_values

class RoleRepository:
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

    def _map_row_to_dict(self, row, cursor):
        if not row:
            return None
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))

    # --- PERUBAHAN ---
    # Menambahkan filter berdasarkan team_id
    def get_all(self, team_id: UUID = None) -> List[dict]:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            # Query dasar
            query = """
                SELECT r.id, r.name, r.description, r.id_team,
                    COALESCE(
                        (SELECT json_agg(json_build_object('id', p.id, 'name', p.name))
                         FROM permissions p
                         JOIN role_permissions rp ON p.id = rp.permission_id
                         WHERE rp.role_id = r.id),
                        '[]'::json
                    ) as permissions
                FROM roles r
            """
            params = []
            # Jika team_id diberikan, tambahkan WHERE clause
            if team_id:
                query += " WHERE r.id_team = %s"
                params.append(str(team_id))
            
            query += " ORDER BY r.name;"
            
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in rows]
        finally:
            cur.close()
            conn.close()

    # --- PERUBAHAN ---
    # Metode ini sekarang mengambil id_team
    def get_by_id(self, role_id: UUID) -> Optional[dict]:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, name, description, id_team FROM roles WHERE id = %s", (str(role_id),))
            return self._map_row_to_dict(cur.fetchone(), cur)
        finally:
            cur.close()
            conn.close()

    # --- BARU ---
    # Metode untuk memeriksa duplikasi nama role dalam satu tim
    def get_by_name_and_team(self, name: str, team_id: UUID) -> Optional[dict]:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT id FROM roles WHERE name = %s AND id_team = %s", (name, str(team_id)))
            return self._map_row_to_dict(cur.fetchone(), cur)
        finally:
            cur.close()
            conn.close()

    # --- PERUBAHAN ---
    # Menyimpan id_team saat membuat role baru
    def create(self, role_data: RoleCreate, team_id: UUID) -> dict:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO roles (name, description, id_team) VALUES (%s, %s, %s) RETURNING id, name, description, id_team",
                (role_data.name, role_data.description, str(team_id))
            )
            new_role = self._map_row_to_dict(cur.fetchone(), cur)
            conn.commit()
            new_role['permissions'] = []
            return new_role
        finally:
            cur.close()
            conn.close()

    def add_permission_to_role(self, role_id: UUID, permission_id: int):
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO role_permissions (role_id, permission_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (str(role_id), permission_id)
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            cur.close()
            conn.close()

    def remove_permission_from_role(self, role_id: UUID, permission_id: int):
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "DELETE FROM role_permissions WHERE role_id = %s AND permission_id = %s",
                (str(role_id), permission_id)
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            cur.close()
            conn.close()
            
    def get_all_permissions(self) -> List[dict]:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, name FROM permissions ORDER BY name")
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in rows]
        finally:
            cur.close()
            conn.close()

    def set_permissions_for_role(self, role_id: UUID, permission_ids: List[int]):
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "DELETE FROM role_permissions WHERE role_id = %s",
                (str(role_id),)
            )
            if permission_ids:
                args_list = [(str(role_id), pid) for pid in permission_ids]
                execute_values(
                    cur,
                    "INSERT INTO role_permissions (role_id, permission_id) VALUES %s ON CONFLICT DO NOTHING",
                    args_list
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()