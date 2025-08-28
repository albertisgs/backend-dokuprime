from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional
from uuid import UUID

class LegalDocumentBase(BaseModel):
    document_name: str
    document_type: str
    staff: str
    team: str
    status: str
    file_path: Optional[str] = None # Sekarang bisa null di awal
    processed_file_path: Optional[str] = None # Kolom baru
    upload_date: date

class LegalDocumentOut(LegalDocumentBase):
    id: UUID

    class Config:
        from_attributes = True

class UploadSuccessResponse(BaseModel):
    message: str
    documents: List[LegalDocumentOut] # Kembalikan list of documents

class StatusResponse(BaseModel):
    status: str
    message: str

class MultipleDeleteRequest(BaseModel):
    doc_ids: List[UUID] = Field(..., min_items=1)

# --- SKEMA BARU UNTUK CALLBACK ---
class DocumentProcessUpdate(BaseModel):
    document_id: UUID
    status: str # "completed" or "failed"
    searchable_pdf_path: Optional[str] = None
    processed_text_path: Optional[str] = None