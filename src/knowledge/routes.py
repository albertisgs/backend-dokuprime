from fastapi import APIRouter
from .handler import KnowledgeHandler

class KnowledgeRoutes:
    def __init__(self):
        self.router = APIRouter()
        self.handler = KnowledgeHandler()
        self.setup_routes()
        print("KnowledgeRoutes Initialized")

    def setup_routes(self):
        @self.router.get("/")
        async def getKnowledges():
            return await self.handler.getKnowledges()
        
        @self.router.get("/knowledge-path")
        async def getRequestById(id: int):
            return await self.handler.getDocumentPath(id=id)