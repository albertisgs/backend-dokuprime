import psycopg2
import os
from typing import List, Optional
from uuid import UUID
from .schemas import RoleCreate, RoleUpdate
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

    def get_all(self) -> List[dict]:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT r.id, r.name, r.description,
                    COALESCE(
                        (SELECT json_agg(json_build_object('id', p.id, 'name', p.name))
                         FROM permissions p
                         JOIN role_permissions rp ON p.id = rp.permission_id
                         WHERE rp.role_id = r.id),
                        '[]'::json
                    ) as permissions
                FROM roles r
                ORDER BY r.name;
            """)
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in rows]
        finally:
            cur.close()
            conn.close()

    def get_by_id(self, role_id: UUID) -> Optional[dict]:
        # Implementasi get_by_id mirip dengan get_all dengan WHERE clause
        # (Dapat ditambahkan jika diperlukan)
        pass

    def create(self, role_data: RoleCreate) -> dict:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO roles (name, description) VALUES (%s, %s) RETURNING id, name, description",
                (role_data.name, role_data.description)
            )
            new_role = self._map_row_to_dict(cur.fetchone(), cur)
            conn.commit()
            new_role['permissions'] = [] # Role baru belum punya permission
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

     # --- TAMBAHKAN METODE BARU DI BAWAH INI ---
    def set_permissions_for_role(self, role_id: UUID, permission_ids: List[int]):
        """
        Mengatur/mengganti semua permission untuk sebuah role.
        Pertama, hapus semua permission yang ada, lalu masukkan yang baru.
        """
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            # 1. Hapus semua permission yang ada untuk role ini
            cur.execute(
                "DELETE FROM role_permissions WHERE role_id = %s",
                (str(role_id),)
            )

            # 2. Jika daftar permission tidak kosong, masukkan semua yang baru
            if permission_ids:
                # Siapkan data untuk bulk insert: [(role_id, pid1), (role_id, pid2), ...]
                args_list = [(str(role_id), pid) for pid in permission_ids]
                
                # Gunakan execute_values untuk bulk insert yang efisien
                execute_values(
                    cur,
                    "INSERT INTO role_permissions (role_id, permission_id) VALUES %s ON CONFLICT DO NOTHING",
                    args_list
                )

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e # Lemparkan error agar bisa ditangani di atasnya
        finally:
            cur.close()
            conn.close()