import os
import uuid
from dotenv import load_dotenv

# --- Impor kelas-kelas yang sudah Anda buat ---
from ..doc_processor.handler import DocumentProcessorHandler as OcrHandler
from ..dify_processor.runner import process_document_with_llm
from ..dify_processor.llm import LLM
from ..dify_processor.dify import DifyDataset

load_dotenv()

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
        self.dify_dataset = DifyDataset(
            base_url=os.getenv("DATASET_BASE_URL"),
            id=os.getenv("DATASET_ID"),
            api_key=os.getenv("DATASET_API_KEY")
        )

        # Konfigurasi path dari .env (sama seperti sebelumnya)
        self.MAIN_API_PUBLIC_PATH = os.getenv('MAIN_API_PUBLIC_PATH')
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
        # Kita panggil metode process_document dari handler Anda.
        # Metode ini akan menyimpan hasilnya ke output_files/ miliknya.
        self.ocr_handler.process_document(input_path)

        # Cari file PDF hasil proses OCR di direktori output OCR
        name, _ = os.path.splitext(original_filename)
        processed_pdf_name = f"{name}_processed.pdf"
        ocr_output_path = os.path.join(self.ocr_handler.output_dir, processed_pdf_name)

        if not os.path.exists(ocr_output_path):
            raise FileNotFoundError(f"File PDF hasil OCR tidak ditemukan di: {ocr_output_path}")

        # Pindahkan file PDF hasil OCR ke direktori public/legal di API Utama
        unique_suffix = str(uuid.uuid4()).split('-')[0]
        final_pdf_filename = f"{name}-{unique_suffix}.pdf"
        final_pdf_path_on_disk = os.path.join(self.output_pdf_dir, final_pdf_filename)
        os.rename(ocr_output_path, final_pdf_path_on_disk)
        
        # Path yang akan disimpan di DB API Utama
        db_pdf_path = f"/legal/{final_pdf_filename}"
        print(f"✅ Proses OCR selesai. File disimpan di: {db_pdf_path}")


        # --- Tahap 2: Proses Analisis & Chunking Dify ---
        print(f"🧠 Memulai proses Dify untuk: {original_filename}")
        # Gunakan PDF yang sudah searchable sebagai input untuk Dify
        # Temporary folder untuk output Dify sebelum diunggah
        dify_temp_output_folder = "dify_temp_output"
        os.makedirs(dify_temp_output_folder, exist_ok=True)

        process_document_with_llm(
            input_folder=self.output_pdf_dir, # Inputnya adalah folder hasil OCR
            output_folder=dify_temp_output_folder,
            file_name=final_pdf_filename, # File spesifik yang baru saja diproses
            llm=self.dify_llm,
            dataset=self.dify_dataset
        )
        
        # Cari file .txt hasil proses Dify
        dify_output_path = os.path.join(dify_temp_output_folder, f"{final_pdf_filename}.txt")
        if not os.path.exists(dify_output_path):
            print("⚠️ Proses Dify tidak menghasilkan file .txt, mungkin karena tidak ada teks.")
            return db_pdf_path, None

        # Pindahkan file .txt hasil Dify ke direktori public/legal_processed di API Utama
        final_txt_filename = f"{name}-{unique_suffix}.txt"
        final_txt_path_on_disk = os.path.join(self.output_txt_dir, final_txt_filename)
        os.rename(dify_output_path, final_txt_path_on_disk)
        
        # Path yang akan disimpan di DB API Utama
        db_txt_path = f"/legal_processed/{final_txt_filename}"
        print(f"✅ Proses Dify selesai. File disimpan di: {db_txt_path}")

        return db_pdf_path, db_txt_path