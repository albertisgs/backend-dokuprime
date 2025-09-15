from pydantic import BaseModel, Field
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

class ImageExtractionOut(ImageExtractionBase):
    id: UUID
    upload_date: date

    class Config:
        from_attributes = True

class ExtractionProcessUpdate(BaseModel):
    document_id: UUID
    status: str
    file_path: Optional[str] = None

class StatusResponse(BaseModel):
    status: str
    message: str