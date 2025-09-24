import os
import psycopg2
from typing import List, Optional
from uuid import UUID

class ImageExtractionRepository:
    def __init__(self):
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
        return dict(zip(columns, row))

    def create(self, doc_data: dict) -> dict:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            sql = """
                INSERT INTO image_extractions (document_name, document_type, staff, team, status)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, upload_date, document_name, document_type, staff, team, status, file_path;
            """
            cur.execute(sql, (
                doc_data['document_name'], doc_data['document_type'],
                doc_data['staff'], doc_data['team'],
                'pending'
            ))
            new_record = cur.fetchone()
            conn.commit()
            columns = [desc[0] for desc in cur.description]
            return dict(zip(columns, new_record))
        finally:
            cur.close()
            conn.close()

    def get_all(self, team_name: Optional[str] = None) -> List[dict]:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            query = "SELECT * FROM image_extractions"
            params = []
            if team_name:
                query += " WHERE team = %s"
                params.append(team_name)
            
            query += " ORDER BY upload_date DESC, id DESC"
            
            cur.execute(query, tuple(params))
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    def get_by_id(self, doc_id: UUID) -> Optional[dict]:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM image_extractions WHERE id = %s", (str(doc_id),))
            record = cur.fetchone()
            if record:
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, record))
            return None
        finally:
            cur.close()
            conn.close()

    def update_status_and_path(self, doc_id: UUID, status: str, file_path: Optional[str]):
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            sql = """
                UPDATE image_extractions
                SET status = %s, file_path = %s
                WHERE id = %s;
            """
            cur.execute(sql, (status, file_path, str(doc_id)))
            conn.commit()
            return cur.rowcount > 0
        finally:
            cur.close()
            conn.close()
            
    def update_status_path_and_category(self, doc_id: UUID, status: str, file_path: Optional[str], category: str):
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            sql = """
                UPDATE image_extractions
                SET status = %s, file_path = %s, category = %s
                WHERE id = %s;
            """
            cur.execute(sql, (status, file_path, category, str(doc_id)))
            conn.commit()
            return cur.rowcount > 0
        finally:
            cur.close()
            conn.close()
            
    def update_extraction_result(self, doc_id: UUID, status: str, file_path: Optional[str], raw_image_path: Optional[str], category: str):
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            sql = """
                UPDATE image_extractions
                SET status = %s, file_path = %s, raw_image_path = %s, category = %s
                WHERE id = %s;
            """
            cur.execute(sql, (status, file_path, raw_image_path, category, str(doc_id)))
            conn.commit()
            return cur.rowcount > 0
        finally:
            cur.close()
            conn.close()

    def delete(self, doc_id: UUID) -> Optional[str]:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM image_extractions WHERE id = %s RETURNING file_path", (str(doc_id),))
            record = cur.fetchone()
            conn.commit()
            return record[0] if record else None
        finally:
            cur.close()
            conn.close()