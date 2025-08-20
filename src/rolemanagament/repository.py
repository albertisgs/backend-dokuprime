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

    def get_all(self, team_id: UUID = None) -> List[dict]:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
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

    def get_by_id(self, role_id: UUID) -> Optional[dict]:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, name, description, id_team FROM roles WHERE id = %s", (str(role_id),))
            return self._map_row_to_dict(cur.fetchone(), cur)
        finally:
            cur.close()
            conn.close()

    def get_by_name_and_team(self, name: str, team_id: UUID) -> Optional[dict]:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT id FROM roles WHERE name = %s AND id_team = %s", (name, str(team_id)))
            return self._map_row_to_dict(cur.fetchone(), cur)
        finally:
            cur.close()
            conn.close()

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

    # --- FUNGSI BARU YANG DITAMBAHKAN ---
    def delete(self, role_id: UUID) -> bool:
        """Menghapus sebuah role berdasarkan ID."""
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            # Hapus juga relasinya di role_permissions terlebih dahulu
            cur.execute("DELETE FROM role_permissions WHERE role_id = %s", (str(role_id),))
            # Baru hapus role-nya
            cur.execute("DELETE FROM roles WHERE id = %s", (str(role_id),))
            conn.commit()
            return cur.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()

    # --- FUNGSI BARU YANG DITAMBAHKAN ---
    def get_user_count_for_role(self, role_id: UUID) -> int:
        """Menghitung berapa banyak user yang menggunakan role ini."""
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM user_management WHERE id_role = %s", (str(role_id),))
            count = cur.fetchone()[0]
            return count
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
            cur.execute("DELETE FROM role_permissions WHERE role_id = %s", (str(role_id),))
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

    def update(self, role_id: UUID, role_data: dict) -> bool:
        """Memperbarui nama dan/atau deskripsi sebuah role."""
        if not role_data:
            return True # Tidak ada yang diupdate, anggap berhasil

        conn = self._get_connection()
        cur = conn.cursor()
        try:
            # Bangun query UPDATE secara dinamis
            set_clause = ", ".join([f"{key} = %s" for key in role_data.keys()])
            values = list(role_data.values())
            values.append(str(role_id))

            query = f"UPDATE roles SET {set_clause} WHERE id = %s"
            
            cur.execute(query, tuple(values))
            conn.commit()
            return cur.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()

    def get_by_id(self, role_id: UUID) -> Optional[dict]:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            # Query ini sekarang mengambil semua detail yang dibutuhkan dalam satu kali jalan
            query = """
                SELECT r.id, r.name, r.description, r.id_team, t.name as team_name,
                    COALESCE(
                        (SELECT json_agg(json_build_object('id', p.id, 'name', p.name))
                         FROM permissions p
                         JOIN role_permissions rp ON p.id = rp.permission_id
                         WHERE rp.role_id = r.id),
                        '[]'::json
                    ) as permissions
                FROM roles r
                LEFT JOIN teams t ON r.id_team = t.id
                WHERE r.id = %s
            """
            cur.execute(query, (str(role_id),))
            
            row = cur.fetchone()
            if not row:
                return None
            
            columns = [desc[0] for desc in cur.description]
            return dict(zip(columns, row))
        finally:
            cur.close()
            conn.close()