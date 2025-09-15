from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks
from .handler import ImageExtractionHandler
from .schemas import ImageExtractionOut, StatusResponse, ExtractionProcessUpdate
from ..utils.sessiondependencies import get_current_user_profile
from ..utils.dependecies import require_access
from typing import List
from uuid import UUID

router = APIRouter(
    tags=["Image Extraction"],
    dependencies=[Depends(require_access("upload-document"))]
)
# Router terpisah untuk callback dari AI service (tanpa autentikasi)
callback_router = APIRouter(tags=["Image Extraction Callback"])

handler = ImageExtractionHandler()

@router.post("/upload")
async def upload_images_for_extraction(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    user: dict = Depends(get_current_user_profile)
):
    return await handler.handle_upload(files, user, background_tasks)

@router.get("/", response_model=List[ImageExtractionOut])
def get_all_extractions(user: dict = Depends(get_current_user_profile)):
    return handler.get_all_extractions(user)

@router.delete("/{doc_id}", response_model=StatusResponse)
def delete_extraction(doc_id: UUID, user: dict = Depends(get_current_user_profile)):
    return handler.delete_extraction(doc_id, user)

# --- ENDPOINT BARU UNTUK CALLBACK ---
@callback_router.post("/update-status", response_model=StatusResponse)
def update_status_from_ai_service(update_data: ExtractionProcessUpdate):
    """
    Webhook untuk dipanggil oleh AI Service setelah konversi selesai.
    """
    return handler.update_document_status(update_data)