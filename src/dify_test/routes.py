# src/dify_test/routes.py

from fastapi import APIRouter
from .handler import DifyTestHandler

# --- PERUBAHAN: Menggunakan struktur Class-based ---
class DifyTestRoutes:
    def __init__(self):
        self.router = APIRouter(
            tags=["Dify Test"],
        )
        self.handler = DifyTestHandler()
        self.setup_routes()

    def setup_routes(self):
        # --- PERBAIKAN: Dekorator harus langsung di atas fungsi ---
        @self.router.get("/connection")
        def test_dify_db_connection():
            """
            Endpoint untuk menguji konektivitas ke database Dify.
            Mengembalikan status koneksi dan beberapa data sampel jika berhasil.
            """
            # Gunakan self.handler untuk memanggil metode dari instance handler
            return self.handler.check_connection()

