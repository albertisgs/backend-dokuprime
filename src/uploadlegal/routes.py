# src/uploadlegal/routes.py

from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks
from .handler import LegalDocumentHandler
from .schemas import UploadSuccessResponse, LegalDocumentOut, StatusResponse, MultipleDeleteRequest, DocumentProcessUpdate
from ..utils.sessiondependencies import get_current_user_profile
from ..utils.dependecies import require_access
from typing import List
from uuid import UUID

router = APIRouter(
    dependencies=[Depends(require_access("upload-document"))],
    tags=["Legal Documents"],
)

sistem_router = APIRouter(tags=["from ai"])

handler = LegalDocumentHandler()

@router.post("/upload", response_model=UploadSuccessResponse)
async def upload_legal_documents(
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user_profile),
    files: List[UploadFile] = File(...)
):
    return await handler.handle_batch_upload(files, user, background_tasks)

@sistem_router.post("/update-status", response_model=StatusResponse)
async def update_document_status_from_ai(update_data: DocumentProcessUpdate):
    """
    Endpoint ini TIDAK untuk dipanggil frontend.
    Ini adalah webhook untuk dipanggil oleh Layanan AI setelah pemrosesan selesai.
    """
    return handler.update_document_status(update_data)

@router.get("/", response_model=List[LegalDocumentOut])
def get_all_legal_documents(user: dict = Depends(get_current_user_profile)):
    return handler.get_all_documents(user)

@router.get("/{doc_id}", response_model=LegalDocumentOut)
def get_legal_document_by_id(doc_id: UUID, user: dict = Depends(get_current_user_profile)):
    return handler.get_document_by_id(doc_id, user)

@router.delete("/{doc_id}", response_model=StatusResponse)
async def delete_legal_document(
    doc_id: UUID, 
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user_profile)
):
    return await handler.delete_document_and_file(doc_id, user, background_tasks)

@router.post("/delete-multiple", response_model=StatusResponse)
async def delete_multiple_legal_documents(
    request: MultipleDeleteRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user_profile)
):
    return await handler.delete_multiple_documents(request.doc_ids, user, background_tasks)