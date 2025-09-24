import os
import shutil
import httpx
from fastapi import UploadFile, HTTPException, BackgroundTasks, status
from .repository import ImageExtractionRepository
from .schemas import ExtractionProcessUpdate
from ..utils.pusher import send_pusher_notification
from uuid import UUID
from typing import List

TEMP_UPLOAD_DIRECTORY = "temp_uploads_images"
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL")
SUPERADMIN_TEAM_ID = os.getenv("SUPERADMIN_TEAM")

ALLOWED_MIME_TYPES = {
    "image/png": "PNG",
    "image/jpeg": "JPG"
}

class ImageExtractionHandler:
    def __init__(self):
        self.repo = ImageExtractionRepository()
        os.makedirs(TEMP_UPLOAD_DIRECTORY, exist_ok=True)

    async def trigger_ai_conversion(self, file_info: dict):
        if not AI_SERVICE_URL:
            print("❌ AI_SERVICE_URL not configured. Skipping processing.")
            return

        try:
            with open(file_info['path'], 'rb') as file_handle:
                files = {'file': (file_info['original_filename'], file_handle, file_info['content_type'])}
                # Data payload sekarang menyertakan document_id
                data = {"document_id": str(file_info['doc_id'])}

                async with httpx.AsyncClient(timeout=300) as client:
                    # --- Panggil endpoint BARU ---
                    target_url = f"{AI_SERVICE_URL}/image-processor/process-image"
                    print(f"🚀 Sending {file_info['original_filename']} to AI service at {target_url}")
                    
                    response = await client.post(target_url, files=files, data=data)
                    response.raise_for_status()
                    print(f"✅ Successfully sent {file_info['original_filename']} to AI service.")
        except httpx.RequestError as e:
            print(f"❌ Error calling AI service for {file_info.get('original_filename')}: {e}")
            # Jika pengiriman gagal, update status di DB menjadi 'failed'
            self.repo.update_status_and_path(file_info['doc_id'], "failed", None)
        finally:
            if os.path.exists(file_info['path']):
                os.remove(file_info['path'])

    async def handle_upload(self, files: List[UploadFile], user: dict, background_tasks: BackgroundTasks):
        if not files:
            raise HTTPException(status_code=400, detail="No files were uploaded.")

        created_docs = []

        for file in files:
            if file.content_type not in ALLOWED_MIME_TYPES:
                print(f"⚠️  Skipping invalid file type: {file.filename}")
                continue

            temp_file_path = os.path.join(TEMP_UPLOAD_DIRECTORY, file.filename)
            
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            doc_data = {
                "document_name": file.filename,
                "document_type": ALLOWED_MIME_TYPES.get(file.content_type, "Unknown"),
                "staff": user.get('username', 'Unknown'),
                "team": user.get('team_name', 'Unknown'),
            }

            try:
                new_document = self.repo.create(doc_data)
                created_docs.append(new_document)
                
                file_to_process = {
                    "path": temp_file_path,
                    "doc_id": new_document['id'],
                    "content_type": file.content_type,
                    "original_filename": file.filename
                }
                # Kirim setiap file sebagai task terpisah
                background_tasks.add_task(self.trigger_ai_conversion, file_to_process)

            except Exception as e:
                os.remove(temp_file_path)
                raise HTTPException(status_code=500, detail=f"Database error for {file.filename}: {e}")

        if not created_docs:
             raise HTTPException(status_code=400, detail="No valid image files to process.")
        
        return {
            "message": f"{len(created_docs)} images accepted for processing.",
            "documents": created_docs
        }

    def update_document_status(self, update_data: ExtractionProcessUpdate):
        """Menerima callback dari AI service untuk update semua data."""
        success = self.repo.update_extraction_result(
            doc_id=update_data.document_id,
            status=update_data.status,
            file_path=update_data.file_path,
            raw_image_path=update_data.raw_image_path, # Kirim path baru ke repo
            category=update_data.category
        )
        if not success:
            raise HTTPException(status_code=404, detail="Document not found for status update.")
        
        # Kirim notifikasi Pusher ke frontend
        send_pusher_notification(
            channel='image-extractions',
            event='status-update',
            data={
                'document_id': str(update_data.document_id),
                'status': update_data.status,
                'category': update_data.category
            }
        )
        return {"status": "success", "message": "Document status updated."}


    def get_all_extractions(self, user: dict):
        is_super_admin = str(user.get("id_team")) == SUPERADMIN_TEAM_ID
        team_to_filter = None if is_super_admin else user.get("team_name")
        return self.repo.get_all(team_name=team_to_filter)

    def delete_extraction(self, doc_id: UUID, user: dict):
        doc = self.repo.get_by_id(doc_id)
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

        is_super_admin = str(user.get("id_team")) == SUPERADMIN_TEAM_ID
        if not is_super_admin and doc.get('team') != user.get('team_name'):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied.")

        file_path = self.repo.delete(doc_id)
        if file_path:
            full_path = os.path.join("public", file_path.lstrip("/"))
            if os.path.exists(full_path):
                os.remove(full_path)
        
        return {"status": "success", "message": "Extraction deleted successfully."}