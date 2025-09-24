from pydantic import BaseModel
from datetime import date
from typing import List, Optional
from uuid import UUID

class ImageExtractionBase(BaseModel):
    document_name: str
    document_type: str
    staff: str
    team: str
    status: str
    file_path: Optional[str] = None
    raw_image_path: Optional[str] = None # Tambahkan field ini
    category: str

class ImageExtractionOut(ImageExtractionBase):
    id: UUID
    upload_date: date

    class Config:
        from_attributes = True

class ExtractionProcessUpdate(BaseModel):
    document_id: UUID
    status: str
    file_path: Optional[str] = None
    raw_image_path: Optional[str] = None # Tambahkan field ini
    category: str

# --- TAMBAHKAN SKEMA INI ---
class StatusResponse(BaseModel):
    status: str
    message: str