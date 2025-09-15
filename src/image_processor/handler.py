# src/image_processor/handler.py
import os
import shutil
import httpx
from uuid import UUID
from fastapi import UploadFile, HTTPException

# Menggunakan kembali logic konversi dari doc_processor
from ..doc_processor import utils as OcrUtils

class ImageProcessorHandler:
    def __init__(self):
        # Direktori sementara di dalam AI service
        self.temp_dir = "image_processor_temp"
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Path ke direktori 'public' di backend utama dari .env
        self.main_api_public_path = os.getenv("MAIN_API_PUBLIC_PATH")
        if not self.main_api_public_path:
            raise ValueError("MAIN_API_PUBLIC_PATH environment variable not set.")

        # Direktori tujuan akhir di backend utama
        self.output_dir = os.path.join(self.main_api_public_path, "extract_results")
        os.makedirs(self.output_dir, exist_ok=True)

        # URL Callback ke backend utama dari .env
        self.callback_url = os.getenv("IMAGE_EXTRACTION_CALLBACK_URL")
        print("ImageProcessorHandler Initialized")

    async def notify_main_api(self, payload: dict):
        """Kirim status kembali ke API Utama."""
        if not self.callback_url:
            print("⚠️ IMAGE_EXTRACTION_CALLBACK_URL not set. Cannot send status update.")
            return

        async with httpx.AsyncClient() as client:
            try:
                print(f"🚀 Sending callback to {self.callback_url} with payload: {payload}")
                response = await client.post(self.callback_url, json=payload, timeout=60)
                response.raise_for_status()
                print(f"✅ Callback sent successfully for doc {payload.get('document_id')}")
            except httpx.RequestError as e:
                print(f"❌ Failed to send callback for doc {payload.get('document_id')}: {e}")

    async def convert_image_to_pdf(self, temp_input_path: str, original_filename: str, document_id: UUID):
        """
        Fungsi utama untuk konversi, penyimpanan, dan callback.
        Sekarang menerima path file, bukan objek UploadFile.
        """
        base_name, _ = os.path.splitext(original_filename)
        output_filename = f"{base_name}.pdf"
        final_output_path = os.path.join(self.output_dir, output_filename)

        try:
            # 1. Lakukan konversi
            print(f"🔬 Converting {original_filename} to PDF...")
            text_content = OcrUtils.extract_text_with_gemini_vision(temp_input_path)
            
            if text_content:
                OcrUtils.create_searchable_pdf(text_content, final_output_path)
                print(f"✅ Conversion successful. PDF saved to: {final_output_path}")

                # 2. Kirim callback sukses
                db_path = f"/extract_results/{output_filename}"
                payload = {
                    "document_id": str(document_id),
                    "status": "completed",
                    "file_path": db_path
                }
                await self.notify_main_api(payload)
            else:
                raise ValueError("Text extraction failed, no content found in image.")

        except Exception as e:
            print(f"❌ Conversion failed for {original_filename}: {e}")
            # 3. Kirim callback gagal
            payload = {"document_id": str(document_id), "status": "failed", "file_path": None}
            await self.notify_main_api(payload)
        finally:
            # 4. Hapus file sementara setelah selesai
            if os.path.exists(temp_input_path):
                os.remove(temp_input_path)