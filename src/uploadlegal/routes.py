from fastapi import APIRouter, Depends, UploadFile, File
from .handler import LegalDocumentHandler
from .schemas import UploadSuccessResponse, LegalDocumentOut, StatusResponse, MultipleDeleteRequest
from ..utils.sessiondependencies import get_current_user_profile
from ..utils.dependecies import require_access
from typing import List
from uuid import UUID

router = APIRouter(
    dependencies=[Depends(require_access("upload-document"))],
    tags=["Legal Documents"],
)

handler = LegalDocumentHandler()

@router.post("/upload", response_model=UploadSuccessResponse)
async def upload_legal_document(
    user: dict = Depends(get_current_user_profile),
    file: UploadFile = File(...)
):
    return handler.upload_and_save_document(file, user)

@router.get("/", response_model=List[LegalDocumentOut])
def get_all_legal_documents():
    return handler.get_all_documents()

@router.get("/{doc_id}", response_model=LegalDocumentOut)
def get_legal_document_by_id(doc_id: UUID):
    return handler.get_document_by_id(doc_id)

@router.delete("/{doc_id}", response_model=StatusResponse)
def delete_legal_document(doc_id: UUID):
    return handler.delete_document_and_file(doc_id)

@router.post("/delete-multiple", response_model=StatusResponse)
def delete_multiple_legal_documents(request: MultipleDeleteRequest):
    return handler.delete_multiple_documents(request.doc_ids)
