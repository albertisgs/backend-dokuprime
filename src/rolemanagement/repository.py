import psycopg2
import os
import json
from typing import List, Optional, Tuple
from uuid import UUID
from .schemas import RoleCreate, RoleUpdate

class RoleRepository:
    def __init__(self):
        # ... (Inisialisasi koneksi database seperti repository lainnya)
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
        role_dict = dict(zip(columns, row))
        # Konversi string JSON dari database menjadi list Python
        if role_dict.get('access') and isinstance(role_dict['access'], str):
            role_dict['access'] = json.loads(role_dict['access'])
        elif not role_dict.get('access'):
            role_dict['access'] = []
        return role_dict

    def get_all(self) -> List[dict]:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, name, access FROM role ORDER BY name")
            rows = cur.fetchall()
            return [self._map_row_to_dict(row, cur) for row in rows]
        finally:
            cur.close()
            conn.close()

    def get_by_id(self, role_id: UUID) -> Optional[dict]:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            # PERBAIKAN: Ubah UUID menjadi string
            cur.execute("SELECT id, name, access FROM role WHERE id = %s", (str(role_id),))
            return self._map_row_to_dict(cur.fetchone(), cur)
        finally:
            cur.close()
            conn.close()

    def create(self, role_data: RoleCreate) -> dict:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            # Konversi list Python menjadi string JSON untuk disimpan di DB
            access_json = json.dumps(role_data.access)
            cur.execute(
                "INSERT INTO role (name, access) VALUES (%s, %s) RETURNING id, name, access",
                (role_data.name, access_json)
            )
            new_role = self._map_row_to_dict(cur.fetchone(), cur)
            conn.commit()
            return new_role
        finally:
            cur.close()
            conn.close()

    def update(self, role_id: UUID, role_data: RoleUpdate) -> Optional[dict]:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            # Dapatkan data role yang ada saat ini
            existing_role = self.get_by_id(role_id)
            if not existing_role:
                return None
            
            update_data = role_data.model_dump(exclude_unset=True)
            
            # Jika ada update 'access', konversi ke JSON string
            if 'access' in update_data:
                update_data['access'] = json.dumps(update_data['access'])

            if not update_data:
                return existing_role # Tidak ada yang diupdate

            set_clause = ", ".join([f"{key} = %s" for key in update_data.keys()])
            values = list(update_data.values())
            # PERBAIKAN: Ubah UUID menjadi string
            values.append(str(role_id))

            query = f"UPDATE role SET {set_clause} WHERE id = %s RETURNING id, name, access"
            
            cur.execute(query, tuple(values))
            updated_role = self._map_row_to_dict(cur.fetchone(), cur)
            conn.commit()
            return updated_role
        finally:
            cur.close()
            conn.close()

    def delete(self, role_id: UUID) -> bool:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            # PERBAIKAN: Ubah UUID menjadi string
            cur.execute("DELETE FROM role WHERE id = %s", (str(role_id),))
            conn.commit()
            return cur.rowcount > 0
        finally:
            cur.close()
            conn.close()

    def get_user_count_and_names(self, role_id: UUID) -> Tuple[int, List[str]]:
        """Menghitung pengguna dan mengambil daftar username mereka."""
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT u.username FROM user_management um
                JOIN users u ON um.id_user::uuid = u.id
                WHERE um.id_role = %s
                """, 
                (str(role_id),)
            )
            rows = cur.fetchall()
            usernames = [row[0] for row in rows]
            return len(usernames), usernames
        finally:
            cur.close()
            conn.close()