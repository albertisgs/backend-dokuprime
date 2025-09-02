# src/dify_test/handler.py

from .repository import DifyTestRepository

class DifyTestHandler:
    def __init__(self):
        self.repo = DifyTestRepository()

    def check_connection(self):
        """Memanggil repository untuk menjalankan tes koneksi."""
        return self.repo.test_connection()
