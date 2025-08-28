# src/processor/routes.py

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from typing import List, Dict
from .handler import DocumentProcessorHandler
from uuid import UUID
import os
import aiofiles

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

    tasks_to_run = []
    for file, doc_id_str in zip(files, document_ids):
        # Create a persistent temporary file path
        temp_file_path = os.path.join(handler.input_dir, f"{UUID(doc_id_str)}-{file.filename}")
        
        # Asynchronously save the uploaded file to our temporary path
        try:
            async with aiofiles.open(temp_file_path, 'wb') as out_file:
                content = await file.read()
                await out_file.write(content)
            
            tasks_to_run.append({
                "temp_path": temp_file_path,
                "original_filename": file.filename,
                "doc_id": UUID(doc_id_str)
            })
        except Exception as e:
            print(f"Error saving file {file.filename}: {e}")
        finally:
            await file.close()

    # Pass the list of task dictionaries (with file paths) to the background function
    if tasks_to_run:
        background_tasks.add_task(handler.process_batch, tasks_to_run)
    
    return {
        "message": f"Accepted {len(tasks_to_run)} files for processing. This will continue in the background."
    }