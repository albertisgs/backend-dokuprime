# src/dify_test/repository.py

import os
import psycopg2
from typing import Dict, Any

class DifyTestRepository:
    def __init__(self):
        # Konfigurasi koneksi untuk DB Dify
        self.dify_user = os.getenv("DIFY_DB_USER")
        self.dify_password = os.getenv("DIFY_DB_PASSWORD")
        self.dify_db_name = os.getenv("DIFY_DB_NAME")
        self.dify_port = os.getenv("DIFY_DB_PORT")
        self.dify_host = os.getenv("DIFY_DB_URL")

    def _get_dify_connection(self):
        """Membuka koneksi ke database Dify."""
        return psycopg2.connect(
            dbname=self.dify_db_name, user=self.dify_user, password=self.dify_password,
            host=self.dify_host, port=self.dify_port
        )

    def test_connection(self) -> Dict[str, Any]:
        """
        Menjalankan query sederhana untuk memeriksa koneksi dan mengambil data sampel.
        """
        conn = None
        try:
            conn = self._get_dify_connection()
            cur = conn.cursor()
            
            # Query untuk mengambil nama aplikasi pertama
            cur.execute("SELECT name FROM public.apps LIMIT 1;")
            app_row = cur.fetchone()
            app_name = app_row[0] if app_row else "No apps found"

            # Query untuk menghitung total percakapan
            cur.execute("SELECT COUNT(*) FROM public.conversations;")
            conversation_count = cur.fetchone()[0]

            cur.close()
            return {
                "status": "success",
                "message": "Successfully connected to Dify database.",
                "data": {
                    "sample_app_name": app_name,
                    "total_conversations": conversation_count
                }
            }
        except psycopg2.Error as e:
            return {
                "status": "error",
                "message": f"Failed to connect to Dify database: {e}"
            }
        finally:
            if conn:
                conn.close()
