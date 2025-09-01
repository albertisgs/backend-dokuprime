# src/uploadlegal/handler.py

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
SUPERADMIN_TEAM_ID = os.getenv("SUPERADMIN_TEAM")

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
        
    async def trigger_dify_deletion(self, document_name: str):
        """Memicu penghapusan dokumen di Dify melalui AI Service."""
        if not AI_SERVICE_URL:
            print("⚠️ AI_SERVICE_URL not configured. Skipping Dify deletion.")
            return

        # Mengambil nama dasar file dan menambahkan ekstensi .txt
        base_name, _ = os.path.splitext(document_name)
        dify_doc_name = f"{base_name}.txt"
        
        delete_url = f"{AI_SERVICE_URL}/delete-document/{dify_doc_name}"
        
        async with httpx.AsyncClient() as client:
            try:
                print(f"🚀 Triggering Dify deletion for: {dify_doc_name}")
                response = await client.delete(delete_url)
                response.raise_for_status() # Akan error jika status bukan 2xx
                print(f"✅ Successfully triggered Dify deletion for {dify_doc_name}. Response: {response.json()}")
            except httpx.RequestError as e:
                print(f"❌ Failed to trigger Dify deletion for {dify_doc_name}: {e}")

    async def trigger_ai_processing(self, files_to_process: list):
        """Kirim file ke Layanan AI dan hapus file temporary."""
        if not AI_SERVICE_URL:
            print("❌ AI_SERVICE_URL not configured. Skipping processing.")
            return
        
        files_to_send = []
        file_handles = [] 

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
        
        finally:
            for handle in file_handles:
                handle.close()
            
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

            temp_file_path = os.path.join(TEMP_UPLOAD_DIRECTORY, f"{file.filename}")
            
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
                os.remove(temp_file_path) 
                raise HTTPException(status_code=500, detail=f"Failed to record document in database: {e}")

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

        send_pusher_notification(
            channel='legal-documents', 
            event='status-update',
            data={
                'document_id': str(update_data.document_id),
                'status': update_data.status
            }
        )

        return {"status": "success", "message": "Document status updated."}

    def get_all_documents(self, user: dict):
        team_id = user.get("id_team")
        is_super_admin = str(team_id) == SUPERADMIN_TEAM_ID
        
        team_to_filter = None
        if not is_super_admin:
            team_to_filter = user.get("team_name")
            
        return self.repo.get_all(team_name=team_to_filter)

    def get_document_by_id(self, doc_id: UUID_TYPE, user: dict):
        doc = self.repo.get_by_id(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        team_id = user.get("id_team")
        is_super_admin = str(team_id) == SUPERADMIN_TEAM_ID
        
        if not is_super_admin and doc.get('team') != user.get('team_name'):
            raise HTTPException(status_code=403, detail="You do not have permission to view this document.")
            
        return doc

    async def delete_document_and_file(self, doc_id: UUID_TYPE, user: dict, background_tasks: BackgroundTasks):
        doc_from_db = self.repo.get_by_id(doc_id)
        
        if doc_from_db:
            team_id = user.get("id_team")
            is_super_admin = str(team_id) == SUPERADMIN_TEAM_ID
            if not is_super_admin and doc_from_db.get('team') != user.get('team_name'):
                raise HTTPException(status_code=403, detail="You do not have permission to delete this document.")
        
            # Tambahkan penghapusan Dify ke background task
            background_tasks.add_task(self.trigger_dify_deletion, doc_from_db['document_name'])

        paths = self.repo.delete(doc_id)
        
        if not paths:
            # Jika dokumen memang tidak ada di DB, anggap berhasil (idempotent)
            return {"status": "success", "message": "Document already deleted or does not exist."}

        # Hapus file dari disk jika path-nya ada
        for file_path in paths:
            if file_path:
                try:
                    full_path = os.path.join("public", file_path.lstrip("/"))
                    if os.path.exists(full_path):
                        os.remove(full_path)
                except Exception as e:
                    print(f"Could not delete file {file_path}: {e}")

        return {"status": "success", "message": "Document, associated files, and Dify entry deletion triggered."}

    async def delete_multiple_documents(self, doc_ids: List[UUID_TYPE], user: dict, background_tasks: BackgroundTasks):
        docs_to_delete = []
        for doc_id in doc_ids:
            doc = self.repo.get_by_id(doc_id)
            if doc:
                docs_to_delete.append(doc)

        if not docs_to_delete:
             raise HTTPException(status_code=404, detail="None of the specified documents were found.")

        # Trigger Dify deletion untuk setiap dokumen
        for doc in docs_to_delete:
            background_tasks.add_task(self.trigger_dify_deletion, doc['document_name'])

        file_paths_list = self.repo.delete_multiple(doc_ids)
        deleted_count = 0
        for paths in file_paths_list:
            for path in paths:
                if path:
                    try:
                        file_path_on_disk = os.path.join("public", path.lstrip("/"))
                        if os.path.exists(file_path_on_disk):
                            os.remove(file_path_on_disk)
                    except Exception as e:
                        print(f"Error deleting file {path} from disk: {e}")
            deleted_count += 1
            
        return {"status": "success", "message": f"{deleted_count} document(s) deletion triggered."}
        # Untuk optimasi, bisa ditambahkan validasi kepemilikan per doc_id di sini
        # Namun untuk saat ini, kita akan langsung mencoba menghapus
        
        file_paths_list = self.repo.delete_multiple(doc_ids)
        if not file_paths_list:
            raise HTTPException(status_code=404, detail="None of the specified documents were found.")

        deleted_count = 0
        for paths in file_paths_list:
            for path in paths:
                if path:
                    try:
                        file_path_on_disk = os.path.join("public", path.lstrip("/"))
                        if os.path.exists(file_path_on_disk):
                            os.remove(file_path_on_disk)
                    except Exception as e:
                        print(f"Error deleting file {path} from disk: {e}")
            deleted_count += 1
            
        return {"status": "success", "message": f"{deleted_count} document(s) and file(s) deleted successfully."}