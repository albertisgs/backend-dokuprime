from pydantic import BaseModel, Field
from datetime import date
from typing import List
from uuid import UUID

class LegalDocumentBase(BaseModel):
    document_name: str
    document_type: str
    staff: str
    team: str
    status: str
    file_path: str
    upload_date: date

class LegalDocumentOut(LegalDocumentBase):
    id: UUID

    class Config:
        from_attributes = True

class UploadSuccessResponse(BaseModel):
    message: str
    document: LegalDocumentOut

class StatusResponse(BaseModel):
    status: str
    message: str

# Skema baru untuk permintaan hapus ganda
class MultipleDeleteRequest(BaseModel):
    doc_ids: List[UUID] = Field(..., min_items=1)
