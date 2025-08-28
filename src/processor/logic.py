from dotenv import load_dotenv

load_dotenv()

class AIServiceLogic:

    async def run_full_process(self, input_path: str, original_filename: str):
        """Menjalankan kedua proses secara berurutan."""
        
        # 1. Proses OCR/Konversi
        db_pdf_path, extracted_text = await self.run_ocr_process(input_path, original_filename)
        
        # 2. Proses Dify
        db_txt_path = await self.run_dify_process(extracted_text, original_filename)

        return db_pdf_path, db_txt_path