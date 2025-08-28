import os
import shutil
import httpx
import uuid
from typing import List, Dict
from fastapi import UploadFile
from uuid import UUID
from .logic import AIServiceLogic

class DocumentProcessorHandler:
    def __init__(self):
        self.logic = AIServiceLogic()
        self.input_dir = "ai_temp_input"
        os.makedirs(self.input_dir, exist_ok=True)
        print("DocumentProcessorHandler Initialized")

    async def notify_main_api(self, doc_id: UUID, status: str, pdf_path: str = None, txt_path: str = None):
        """Kirim status kembali ke API Utama."""
        if not self.logic.MAIN_API_CALLBACK_URL:
            print("❌ MAIN_API_CALLBACK_URL not set. Cannot send status update.")
            return

        payload = {
            "document_id": str(doc_id),
            "status": status,
            "searchable_pdf_path": pdf_path,
            "processed_text_path": txt_path,
        }
        
        async with httpx.AsyncClient() as client:
            try:
                print(f"🚀 Sending callback for doc {doc_id} with status: {status}")
                await client.post(self.logic.MAIN_API_CALLBACK_URL, json=payload, timeout=60)
            except httpx.RequestError as e:
                print(f"❌ Failed to send callback for doc {doc_id}: {e}")

    async def process_batch(self, files: List[UploadFile], doc_id_map: Dict[str, UUID]):
        """Simpan file dari batch dan proses satu per satu."""
        for file in files:
            doc_id = doc_id_map.get(file.filename)
            if not doc_id:
                print(f"⚠️ Warning: No document ID found for file {file.filename}. Skipping.")
                continue

            # Simpan file sementara untuk diproses
            temp_input_path = os.path.join(self.input_dir, f"{uuid.uuid4()}-{file.filename}")
            
            try:
                with open(temp_input_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                print(f"\n--- Starting AI processing for: {file.filename} (ID: {doc_id}) ---")
                
                # Jalankan alur logika pemrosesan
                pdf_path, txt_path = await self.logic.run_full_process(temp_input_path, original_filename=file.filename)
                
                # Kirim notifikasi sukses
                await self.notify_main_api(doc_id, "completed", pdf_path, txt_path)

            except Exception as e:
                print(f"❌ Full process failed for {file.filename}: {e}")
                # Kirim notifikasi gagal
                await self.notify_main_api(doc_id, "failed")
            finally:
                if os.path.exists(temp_input_path):
                    os.remove(temp_input_path) # Hapus file input temp
                file.file.close()