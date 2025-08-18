from fastapi import APIRouter, Depends
from .handler import KnowledgeHandler
# Import dependency yang dibutuhkan untuk pengecekan hak akses
from ..utils.dependecies import require_access

class KnowledgeRoutes:
    def __init__(self):
        self.router = APIRouter(
            dependencies=[Depends(require_access("knowledge-base"))]
        )
        self.handler = KnowledgeHandler()
        self.setup_routes()
        print("KnowledgeRoutes Initialized and Secured")

    def setup_routes(self):
        @self.router.get("/")
        async def getKnowledges():
            # Endpoint ini sekarang aman
            return await self.handler.getKnowledges()
        
        @self.router.get("/knowledge-path")
        async def getRequestById(id: int):
            # Endpoint ini juga sekarang aman
            return await self.handler.getDocumentPath(id=id)
