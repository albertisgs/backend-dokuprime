import os
import shutil
import uuid
from fastapi import UploadFile, HTTPException, status
from .repository import LegalRepository
from uuid import UUID as UUID_TYPE
from typing import List

UPLOAD_DIRECTORY = "public/legal"

# Daftar tipe file yang diizinkan (MIME Type -> Nama Tampilan)
ALLOWED_MIME_TYPES = {
    "application/pdf": "PDF",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "DOCX",
    "image/png": "PNG",
    "image/jpeg": "JPG"
}

class LegalDocumentHandler:
    def __init__(self):
        self.repo = LegalRepository()
        os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

    def get_all_documents(self):
        return self.repo.get_all()

    def get_document_by_id(self, doc_id: UUID_TYPE):
        doc = self.repo.get_by_id(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc

    def upload_and_save_document(self, file: UploadFile, user: dict):
        # --- PERUBAHAN DI SINI ---
        # 1. Validasi tipe file berdasarkan daftar yang diizinkan
        if file.content_type not in ALLOWED_MIME_TYPES:
            allowed_types_str = ", ".join(ALLOWED_MIME_TYPES.values())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types are: {allowed_types_str}."
            )

        # 2. Buat nama file unik dengan format nama-asli-idunik.ekstensi
        filename_without_ext, file_extension = os.path.splitext(file.filename)
        unique_suffix = str(uuid.uuid4()).split('-')[0]
        unique_filename = f"{filename_without_ext}-{unique_suffix}{file_extension}"
        
        file_path_on_disk = os.path.join(UPLOAD_DIRECTORY, unique_filename)
        db_path = f"/legal/{unique_filename}"

        if os.path.exists(file_path_on_disk):
            raise HTTPException(status_code=409, detail="A file with this unique ID already exists. Please try again.")

        try:
            with open(file_path_on_disk, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Could not save file: {e}")
        finally:
            file.file.close()

        # 3. Simpan nama file asli di DB, tapi path menggunakan nama unik
        doc_data = {
            "document_name": file.filename,
            "document_type": ALLOWED_MIME_TYPES.get(file.content_type, "Unknown"), # Dapatkan tipe dari dictionary
            "staff": user.get('username', 'Unknown'),
            "team": user.get('role_name', 'Unknown'),
            "status": "Completed",
            "file_path": db_path
        }
        
        try:
            new_document = self.repo.create(doc_data)
            return {
                "message": "File uploaded and recorded successfully.",
                "document": new_document
            }
        except Exception as e:
            os.remove(file_path_on_disk)
            raise HTTPException(status_code=500, detail=f"Failed to record document in database: {e}")

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
        """Menghapus beberapa dokumen dan file terkait."""
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