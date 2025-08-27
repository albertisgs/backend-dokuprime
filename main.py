# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
from src.doc_processor.routes import router as doc_processor_router

# Load environment variables from .env file
load_dotenv()

class DocProcessorAPI:
    def __init__(self):
        self.app = FastAPI(
            title="Document Processor API",
            description="An API to convert documents (PDF, DOCX, images) into searchable PDFs using Ollama.",
            version="1.0.0"
        )
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.include_routers()

    def include_routers(self):
        self.app.include_router(doc_processor_router, prefix="/api/doc-processor", tags=["Document Processing"])

    def run(self):
        uvicorn.run(
            self.app,
            host="0.0.0.0", # Listen on all available network interfaces
            port=9798, # Using a different port than your other API
        )

doc_processor_api = DocProcessorAPI()
app = doc_processor_api.app

if __name__ == "__main__":
    doc_processor_api.run()