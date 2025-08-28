from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from typing import List
from .handler import DocumentProcessorHandler
from uuid import UUID

router = APIRouter()
handler = DocumentProcessorHandler()

@router.post("/process-batch")
async def process_document_batch(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    document_ids: List[str] = Form(...)
):
    if len(files) != len(document_ids):
        raise HTTPException(status_code=400, detail="The number of files and document_ids must be the same.")

    # Buat dictionary untuk memetakan nama file ke ID dokumen
    # Asumsi nama file unik dalam satu batch
    doc_id_map = {file.filename: UUID(doc_id) for file, doc_id in zip(files, document_ids)}

    # Jalankan pemrosesan di latar belakang
    background_tasks.add_task(handler.process_batch, files, doc_id_map)
    
    return {
        "message": f"Accepted {len(files)} files for processing. This will continue in the background."
    }