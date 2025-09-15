# src/image_processor/schemas.py
from pydantic import BaseModel
from uuid import UUID

class ImageProcessRequest(BaseModel):
    document_id: UUID

class StatusUpdatePayload(BaseModel):
    document_id: UUID
    status: str
    file_path: str | None = None