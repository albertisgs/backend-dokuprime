from fastapi import APIRouter, Depends
from .handler import RequestHandler
from ..utils.dependecies import require_access

class RequestRoutes:
    def __init__(self):
        self.router = APIRouter(
             dependencies=[Depends(require_access("prompt-management"))]
        )
        self.handler = RequestHandler()
        self.setup_routes()
        print("RequestRoutes Initialized")

    def setup_routes(self):
        @self.router.post("/")
        async def addPrompt(new_request: dict):
            return await self.handler.addPrompt(new_request)
        
        @self.router.get("/")
        async def getRequests():
            return await self.handler.getRequests()
        
        @self.router.get("/get-detail")
        async def getRequestById(id: int):
            return await self.handler.getRequestsById(id=id)
        