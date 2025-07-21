import os
from dotenv import load_dotenv
from .repository import KnowledgeRepository
from fastapi.responses import FileResponse

class KnowledgeHandler:
    def __init__(self):
        self.repo = KnowledgeRepository()
        print("Handler Initiated")
    
    async def getKnowledges(self):
        print("Entering getKnowledges function")

        knowledges = await self.repo.getKnowledgesRepo()

        print("Exiting getKnowledges function")
        return {"status": 200, "message": "Operation Successfull!", "data": knowledges}
    
    async def getDocumentPath(self, id: int):
        print("Entering getDocumentPath function")

        doc_path = await self.repo.getDocumentPathRepo(id=id)
        if not doc_path:
            return {"status": 404, "message": "document not found"}
        
        base_dir = os.path.abspath(os.path.dirname(__file__)).rsplit("src", 1)[0]

        relative_path = doc_path['file_path'].lstrip("/") 
        file_path = os.path.join(base_dir, relative_path)
        filename = doc_path.get('report_title', 'downloaded_file') + ".pdf"
        print(filename)

        if not os.path.isfile(file_path):
            return {'status': 404, 'message': 'File not found on server'}

        print("Exiting getDocumentPath function")
        return FileResponse(path=file_path, filename=filename, media_type='application/pdf')