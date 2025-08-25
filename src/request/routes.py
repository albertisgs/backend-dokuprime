# src/request/routes.py

from fastapi import APIRouter, Depends, Body
from .handler import RequestHandler
from ..utils.dependecies import require_permission # Ganti nama import
from ..utils.sessiondependencies import get_current_user_profile

class RequestRoutes:
    def __init__(self):
        # Hapus dependency di level router agar bisa diterapkan per-endpoint
        self.router = APIRouter()
        self.handler = RequestHandler()
        self.setup_routes()
        print("RequestRoutes Initialized")

    def setup_routes(self):
        # Rute untuk menambah (Create)
        @self.router.post("/", dependencies=[Depends(require_permission("prompt-management:create"))])
        async def addPrompt(new_request: dict, current_user: dict = Depends(get_current_user_profile)):
            # Teruskan current_user ke handler
            return await self.handler.addPrompt(new_request, current_user)
        
        @self.router.get("/", dependencies=[Depends(require_permission("prompt-management:read"))])
        async def getRequests(current_user: dict = Depends(get_current_user_profile)):
            # Teruskan current_user ke handler
            return await self.handler.getRequests(current_user)
        
        # Rute untuk membaca detail (Read)
        @self.router.get("/get-detail", dependencies=[Depends(require_permission("prompt-management:read"))])
        async def getRequestById(id: int):
            return await self.handler.getRequestsById(id=id)

        # --- RUTE BARU: Update ---
        @self.router.put("/{request_id}", dependencies=[Depends(require_permission("prompt-management:update"))])
        async def updatePrompt(request_id: int, data: dict = Body(...)):
            return await self.handler.updatePrompt(id=request_id, data_to_update=data)

        # --- RUTE BARU: Delete ---
        @self.router.delete("/{request_id}", dependencies=[Depends(require_permission("prompt-management:delete"))])
        async def deletePrompt(request_id: int):
            return await self.handler.deletePrompt(id=request_id)
            
        # --- RUTE BARU: Approve ---
        @self.router.post("/{request_id}/approve", dependencies=[Depends(require_permission("prompt-management:manager"))])
        async def approveRequest(request_id: int):
            return await self.handler.approveRequest(id=request_id)
            
        # --- RUTE BARU: Reject ---
        @self.router.post("/{request_id}/reject", dependencies=[Depends(require_permission("prompt-management:manager"))])
        async def rejectRequest(request_id: int):
            return await self.handler.rejectRequest(id=request_id)