import psycopg2
import os
import json
from typing import List, Optional, Tuple
from uuid import UUID
from .schemas import TeamCreate, TeamUpdate

class TeamRepository:
    def __init__(self):
        # ... (Inisialisasi koneksi database seperti repository lainnya)
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.db_name = os.getenv("DB_NAME")
        self.port = os.getenv("DB_PORT")
        self.host = os.getenv("DB_URL")

    def _get_connection(self):
        return psycopg2.connect(
            dbname=self.db_name, user=self.user, password=self.password,
            host=self.host, port=self.port
        )

    def _map_row_to_dict(self, row, cursor):
        if not row:
            return None
        columns = [desc[0] for desc in cursor.description]
        team_dict = dict(zip(columns, row))
        # Konversi string JSON dari database menjadi list Python
        if team_dict.get('access') and isinstance(team_dict['access'], str):
            team_dict['access'] = json.loads(team_dict['access'])
        elif not team_dict.get('access'):
            team_dict['access'] = []
        return team_dict

    def get_all(self) -> List[dict]:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, name, access FROM teams ORDER BY name")
            rows = cur.fetchall()
            return [self._map_row_to_dict(row, cur) for row in rows]
        finally:
            cur.close()
            conn.close()

    def get_by_id(self, team_id: UUID) -> Optional[dict]:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            # PERBAIKAN: Ubah UUID menjadi string
            cur.execute("SELECT id, name, access FROM teams WHERE id = %s", (str(team_id),))
            return self._map_row_to_dict(cur.fetchone(), cur)
        finally:
            cur.close()
            conn.close()

    def create(self, team_data: TeamCreate) -> dict:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            # Konversi list Python menjadi string JSON untuk disimpan di DB
            access_json = json.dumps(team_data.access)
            cur.execute(
                "INSERT INTO teams (name, access) VALUES (%s, %s) RETURNING id, name, access",
                (team_data.name, access_json)
            )
            new_team = self._map_row_to_dict(cur.fetchone(), cur)
            conn.commit()
            return new_team
        finally:
            cur.close()
            conn.close()

    def update(self, team_id: UUID, team_data: TeamUpdate) -> Optional[dict]:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            # Dapatkan data team yang ada saat ini
            existing_team = self.get_by_id(team_id)
            if not existing_team:
                return None
            
            update_data = team_data.model_dump(exclude_unset=True)
            
            # Jika ada update 'access', konversi ke JSON string
            if 'access' in update_data:
                update_data['access'] = json.dumps(update_data['access'])

            if not update_data:
                return existing_team # Tidak ada yang diupdate

            set_clause = ", ".join([f"{key} = %s" for key in update_data.keys()])
            values = list(update_data.values())
            # PERBAIKAN: Ubah UUID menjadi string
            values.append(str(team_id))

            query = f"UPDATE teams SET {set_clause} WHERE id = %s RETURNING id, name, access"
            
            cur.execute(query, tuple(values))
            updated_team = self._map_row_to_dict(cur.fetchone(), cur)
            conn.commit()
            return updated_team
        finally:
            cur.close()
            conn.close()

    def delete(self, team_id: UUID) -> bool:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            # PERBAIKAN: Ubah UUID menjadi string
            cur.execute("DELETE FROM teams WHERE id = %s", (str(team_id),))
            conn.commit()
            return cur.rowcount > 0
        finally:
            cur.close()
            conn.close()

    def get_user_count_and_names(self, team_id: UUID) -> Tuple[int, List[str]]:
        """Menghitung pengguna dan mengambil daftar username mereka."""
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT u.username FROM user_management um
                JOIN users u ON um.id_user::uuid = u.id
                WHERE um.id_team = %s
                """, 
                (str(team_id),)
            )
            rows = cur.fetchall()
            usernames = [row[0] for row in rows]
            return len(usernames), usernames
        finally:
            cur.close()
            conn.close()