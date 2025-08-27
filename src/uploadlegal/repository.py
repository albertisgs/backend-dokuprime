import os
import psycopg2
from dotenv import load_dotenv
from typing import List, Optional
from uuid import UUID

load_dotenv()

class LegalRepository:
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

    def create(self, doc_data: dict) -> dict:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            sql = """
                INSERT INTO legal_documents (document_name, document_type, staff, team, status, file_path)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, upload_date, document_name, document_type, staff, team, status, file_path;
            """
            cur.execute(sql, (
                doc_data['document_name'], doc_data['document_type'],
                doc_data['staff'], doc_data['team'],
                doc_data['status'], doc_data['file_path']
            ))
            new_record = cur.fetchone()
            conn.commit()
            columns = [desc[0] for desc in cur.description]
            return dict(zip(columns, new_record))
        finally:
            cur.close()
            conn.close()

    def get_all(self) -> List[dict]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM legal_documents ORDER BY upload_date DESC, id DESC")
        columns = [desc[0] for desc in cur.description]
        data = [dict(zip(columns, row)) for row in cur.fetchall()]
        cur.close()
        conn.close()
        return data

    def get_by_id(self, doc_id: UUID) -> Optional[dict]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM legal_documents WHERE id = %s", (str(doc_id),))
        record = cur.fetchone()
        cur.close()
        conn.close()
        if record:
            columns = [desc[0] for desc in cur.description]
            return dict(zip(columns, record))
        return None

    def delete(self, doc_id: UUID) -> Optional[str]:
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM legal_documents WHERE id = %s RETURNING file_path", (str(doc_id),))
            record = cur.fetchone()
            conn.commit()
            if record:
                return record[0]
            return None
        finally:
            cur.close()
            conn.close()

    def delete_multiple(self, doc_ids: List[UUID]) -> List[str]:
        """Menghapus beberapa dokumen berdasarkan daftar ID."""
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            ids_list = [str(doc_id) for doc_id in doc_ids]
            
            # PERBAIKAN: Tambahkan type cast ::uuid[] pada placeholder
            query = "DELETE FROM legal_documents WHERE id = ANY(%s::uuid[]) RETURNING file_path"
            cur.execute(query, (ids_list,))
            
            file_paths = [row[0] for row in cur.fetchall()]
            conn.commit()
            return file_paths
        finally:
            cur.close()
            conn.close()