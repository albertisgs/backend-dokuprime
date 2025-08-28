import os
import shutil
import uuid
import httpx
from fastapi import UploadFile, HTTPException, status, BackgroundTasks
from .repository import LegalRepository
from .schemas import DocumentProcessUpdate
from ..utils.pusher import send_pusher_notification
from uuid import UUID as UUID_TYPE
from typing import List

TEMP_UPLOAD_DIRECTORY = "temp_uploads"
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL")

ALLOWED_MIME_TYPES = {
    "application/pdf": "PDF",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "DOCX",
    "image/png": "PNG",
    "image/jpeg": "JPG"
}

class LegalDocumentHandler:
    def __init__(self):
        self.repo = LegalRepository()
        os.makedirs(TEMP_UPLOAD_DIRECTORY, exist_ok=True)

    async def trigger_ai_processing(self, files_to_process: list):
        """Kirim file ke Layanan AI dan hapus file temporary."""
        if not AI_SERVICE_URL:
            print("❌ AI_SERVICE_URL not configured. Skipping processing.")
            return
        
        # --- PERBAIKAN DI SINI ---
        # Kita akan membangun daftar file dengan cara yang lebih aman
        files_to_send = []
        file_handles = [] # Untuk menyimpan file handle yang perlu ditutup

        try:
            for f in files_to_process:
                file_handle = open(f['path'], 'rb')
                file_handles.append(file_handle)
                files_to_send.append(
                    ("files", (os.path.basename(f['path']), file_handle, f['content_type']))
                )
            
            doc_ids = [str(f['doc_id']) for f in files_to_process]
            data = {"document_ids": doc_ids}

            async with httpx.AsyncClient(timeout=300) as client:
                print(f"🚀 Sending {len(files_to_send)} files to AI service at {AI_SERVICE_URL}/process-batch")
                response = await client.post(f"{AI_SERVICE_URL}/process-batch", files=files_to_send, data=data)
                response.raise_for_status()
                print(f"✅ Successfully sent {len(files_to_process)} files to AI service.")

        except httpx.RequestError as e:
            print(f"❌ Error calling AI service: {e}")
            # Anda bisa menambahkan logika untuk menandai dokumen sebagai gagal di sini
            # misalnya dengan memanggil repo.update_status_and_paths(...)
        
        finally:
            # Pastikan semua file handle ditutup
            for handle in file_handles:
                handle.close()
            
            # Sekarang aman untuk menghapus file
            for f in files_to_process:
                if os.path.exists(f['path']):
                    try:
                        os.remove(f['path'])
                    except OSError as e:
                        print(f"Error removing file {f['path']}: {e}")

    async def handle_batch_upload(self, files: List[UploadFile], user: dict, background_tasks: BackgroundTasks):
        """Menangani unggahan batch, menyimpan ke temp, dan memicu pemrosesan AI."""
        if not files:
            raise HTTPException(status_code=400, detail="No files were uploaded.")

        created_docs = []
        files_to_process = []

        for file in files:
            if file.content_type not in ALLOWED_MIME_TYPES:
                raise HTTPException(
                    status_code=400,
                    detail=f"File '{file.filename}' has an invalid type. Allowed: {', '.join(ALLOWED_MIME_TYPES.values())}"
                )

            temp_file_path = os.path.join(TEMP_UPLOAD_DIRECTORY, f"{uuid.uuid4()}-{file.filename}")
            
            try:
                with open(temp_file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
            finally:
                file.file.close()

            doc_data = {
                "document_name": file.filename,
                "document_type": ALLOWED_MIME_TYPES.get(file.content_type, "Unknown"),
                "staff": user.get('username', 'Unknown'),
                "team": user.get('team_name', 'Unknown'),
                "status": "pending",
            }

            try:
                new_document = self.repo.create(doc_data)
                created_docs.append(new_document)
                files_to_process.append({
                    "path": temp_file_path, 
                    "doc_id": new_document['id'],
                    "content_type": file.content_type
                })
            except Exception as e:
                os.remove(temp_file_path) # Hapus file temp jika Gagal membuat entri DB
                raise HTTPException(status_code=500, detail=f"Failed to record document in database: {e}")

        # Jalankan pengiriman ke AI service di latar belakang
        background_tasks.add_task(self.trigger_ai_processing, files_to_process)

        return {
            "message": f"{len(created_docs)} files uploaded and are now processing.",
            "documents": created_docs
        }
    
    def update_document_status(self, update_data: DocumentProcessUpdate):
        """Menerima callback dari AI service untuk update status."""
        success = self.repo.update_status_and_paths(
            doc_id=update_data.document_id,
            status=update_data.status,
            pdf_path=update_data.searchable_pdf_path,
            txt_path=update_data.processed_text_path
        )
        if not success:
            raise HTTPException(status_code=404, detail="Document not found for status update.")

        # Kirim notifikasi Pusher ke frontend
        send_pusher_notification(
            channel='legal-documents', # Channel general untuk update
            event='status-update',
            data={
                'document_id': str(update_data.document_id),
                'status': update_data.status
            }
        )

        return {"status": "success", "message": "Document status updated."}

    def get_all_documents(self):
        return self.repo.get_all()

    def get_document_by_id(self, doc_id: UUID_TYPE):
        doc = self.repo.get_by_id(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc

    def delete_document_and_file(self, doc_id: UUID_TYPE):
        file_path_from_db = self.repo.delete(doc_id)
        if not file_path_from_db:
            raise HTTPException(status_code=404, detail="Document not found in database.")
        try:
            file_path_on_disk = os.path.join("public", file_path_from_db.lstrip("/"))
            if os.path.exists(file_path_on_disk):
                os.remove(file_path_on_disk)
        except Exception as e:
            print(f"Error deleting file from disk: {e}")
        return {"status": "success", "message": "Document and file deleted successfully."}

    def delete_multiple_documents(self, doc_ids: List[UUID_TYPE]):
        file_paths = self.repo.delete_multiple(doc_ids)
        if not file_paths:
            raise HTTPException(status_code=404, detail="None of the specified documents were found.")
        deleted_count = 0
        for path in file_paths:
            try:
                file_path_on_disk = os.path.join("public", path.lstrip("/"))
                if os.path.exists(file_path_on_disk):
                    os.remove(file_path_on_disk)
                    deleted_count += 1
            except Exception as e:
                print(f"Error deleting file {path} from disk: {e}")
        return {"status": "success", "message": f"{deleted_count} document(s) and file(s) deleted successfully."}