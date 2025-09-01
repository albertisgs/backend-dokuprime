# src/processor/logic.py

import os
import uuid
from dotenv import load_dotenv
import json
import requests
from pathlib import Path

# --- Impor kelas-kelas yang sudah Anda buat ---
from ..doc_processor.handler import DocumentProcessorHandler as OcrHandler
from ..dify_processor.runner import process_document_with_llm
from ..dify_processor.llm import LLM
# Impor DifyDataset yang asli untuk di-override
from ..dify_processor.dify import DifyDataset

load_dotenv()

# --- FIX: Custom DifyDataset Class ---
# Kelas kustom ini mewarisi dari DifyDataset yang asli tetapi menimpa
# metode unggah untuk memperbaiki nama file sebelum dikirim ke Dify API.
# Ini dilakukan untuk mematuhi batasan untuk tidak mengubah modul dify_processor.
class CustomDifyDataset(DifyDataset):
    def upload_document_to_dataset(self, file_path):
        """
        Mengunggah dokumen ke dataset Dify, memastikan nama file
        diperbaiki dari 'name.pdf.txt' menjadi 'name.txt' untuk proses unggah.
        """
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Perbaiki nama file: "file.pdf.txt" -> "file.txt"
        correct_stem = Path(file_path_obj.stem).stem
        correct_filename = f"{correct_stem}.txt"

        print(f"Uploading to Dify with corrected filename: {correct_filename} (original on disk: {file_path_obj.name})")

        # Sisa dari metode ini adalah salinan dari implementasi asli,
        # tetapi menggunakan `correct_filename` dalam payload 'files'.
        url = f"{self.base_url}/datasets/{self.id}/document/create-by-file"
        headers = { 'Authorization': f'Bearer {self.api_key}' }
        files = {
            'file': (correct_filename, open(file_path, 'rb'), 'text/plain')
        }
        data_payload = {
            "indexing_technique": "high_quality",
            "process_rule": {
                "rules": {
                    "pre_processing_rules": [
                        {"id": "remove_extra_spaces", "enabled": False},
                        {"id": "remove_urls_emails", "enabled": False}
                    ],
                    "segmentation": {
                        "separator": "===[TEXT]===",
                        "max_tokens": 4000,
                        "chunk_overlap": 400
                    }
                },
                "mode": "custom"
            }
        }
        data = { 'data': (None, json.dumps(data_payload), 'text/plain') }

        try:
            response = requests.post(url, headers=headers, files=files, data=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status code: {e.response.status_code}")
                print(f"Response text: {e.response.text}")
            raise
        finally:
            if 'file' in files:
                files['file'][1].close()


class AIServiceLogic:
    def __init__(self):
        # Inisialisasi handler OCR
        self.ocr_handler = OcrHandler()
        
        # Inisialisasi komponen untuk Dify dari .env
        self.dify_llm = LLM(
            llm_base_url=os.getenv("LLM_BASE_URL"),
            llm_model=os.getenv("LLM_MODEL"),
            llm_api_key=os.getenv("LLM_API_KEY"),
            embedding_base_url=os.getenv("EMBEDDINGS_BASE_URL"),
            embedding_model=os.getenv("EMBEDDINGS_MODEL"),
        )
        
        # --- FIX: Gunakan kelas CustomDifyDataset ---
        self.dify_dataset = CustomDifyDataset(
            base_url=os.getenv("DATASET_BASE_URL"),
            id=os.getenv("DATASET_ID"),
            api_key=os.getenv("DATASET_API_KEY")
        )

        # Konfigurasi path dari .env
        self.MAIN_API_PUBLIC_PATH = os.getenv('MAIN_API_PUBLIC_PATH')
        self.MAIN_API_CALLBACK_URL = os.getenv('MAIN_API_CALLBACK_URL') # Pastikan ini ada
        if not self.MAIN_API_PUBLIC_PATH or not os.path.isdir(self.MAIN_API_PUBLIC_PATH):
            raise ValueError("MAIN_API_PUBLIC_PATH is not configured or does not exist.")
            
        self.output_pdf_dir = os.path.join(self.MAIN_API_PUBLIC_PATH, "legal")
        self.output_txt_dir = os.path.join(self.MAIN_API_PUBLIC_PATH, "legal_processed")
        os.makedirs(self.output_pdf_dir, exist_ok=True)
        os.makedirs(self.output_txt_dir, exist_ok=True)


    async def run_full_process(self, input_path: str, original_filename: str):
        """
        Menjalankan kedua proses secara berurutan dengan mengintegrasikan kelas Anda.
        """
        
        # --- Tahap 1: Proses OCR/Konversi Dokumen ---
        print(f"🔬 Memulai proses OCR untuk: {original_filename}")
        self.ocr_handler.process_document(input_path)

        # --- FIX IS HERE ---
        # Base the output filename on the ACTUAL file that was processed (input_path),
        # not the original_filename from before it was renamed.
        processed_basename = os.path.basename(input_path)
        name, _ = os.path.splitext(processed_basename)
        processed_pdf_name = f"{name}_processed.pdf"
        ocr_output_path = os.path.join(self.ocr_handler.output_dir, processed_pdf_name)
        # --- END FIX ---

        if not os.path.exists(ocr_output_path):
            raise FileNotFoundError(f"File PDF hasil OCR tidak ditemukan di: {ocr_output_path}")

        # Pindahkan file PDF hasil OCR ke direktori public/legal di API Utama
        # We use the original_filename here to keep the final name clean
        original_name_base, _ = os.path.splitext(original_filename)
        # unique_suffix = str(uuid.uuid4()).split('-')[0]
        # final_pdf_filename = f"{original_name_base}-{unique_suffix}.pdf"
        final_pdf_filename = f"{original_name_base}.pdf"
        final_pdf_path_on_disk = os.path.join(self.output_pdf_dir, final_pdf_filename)
        os.rename(ocr_output_path, final_pdf_path_on_disk)
        
        db_pdf_path = f"/legal/{final_pdf_filename}"
        print(f"✅ Proses OCR selesai. File disimpan di: {db_pdf_path}")


        # --- Tahap 2: Proses Analisis & Chunking Dify ---
        print(f"🧠 Memulai proses Dify untuk: {original_filename}")
        dify_temp_output_folder = "dify_temp_output"
        os.makedirs(dify_temp_output_folder, exist_ok=True)

        process_document_with_llm(
            input_folder=self.output_pdf_dir,
            output_folder=dify_temp_output_folder,
            file_name=final_pdf_filename,
            llm=self.dify_llm,
            dataset=self.dify_dataset
        )
        
        dify_output_path = os.path.join(dify_temp_output_folder, f"{final_pdf_filename}.txt")
        if not os.path.exists(dify_output_path):
            print("⚠️ Proses Dify tidak menghasilkan file .txt, mungkin karena tidak ada teks.")
            return db_pdf_path, None

        # --- PERBAIKAN DI SINI ---
        # Gunakan 'original_name_base' untuk membuat nama file .txt agar tidak ada ekstensi .pdf
        final_txt_filename = f"{original_name_base}.txt"
        final_txt_path_on_disk = os.path.join(self.output_txt_dir, final_txt_filename)
        os.rename(dify_output_path, final_txt_path_on_disk)
        
        db_txt_path = f"/legal_processed/{final_txt_filename}"
        print(f"✅ Proses Dify selesai. File disimpan di: {db_txt_path}")

        return db_pdf_path, db_txt_path