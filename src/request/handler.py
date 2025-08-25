import os
from dotenv import load_dotenv
from .repository import RequestRepository
from fastapi import HTTPException 
from src.utils.pusher import send_pusher_notification

class RequestHandler:
    def __init__(self):
        self.repo = RequestRepository()
        print("Handler Initiated")

     # --- MODIFIKASI FUNGSI INI ---
    async def addPrompt(self, new_request: dict, current_user: dict):
        print("Entering addPrompt function")
        # Ambil user_request dan team dari profil pengguna yang login, bukan dari input manual
        user_request_item = current_user.get("username", "Unknown User")
        team_item = current_user.get("team_name", "Unknown Team")
        
        # Ambil data sisa dari payload
        usecase_name_item = new_request["usecase_name"]
        priority_item = new_request["priority"]
        reason_item = new_request["reason"]
        prompt_item = new_request["prompt"]

        # Kirim data yang sudah divalidasi ke repository
        await self.repo.addPromptRepo(
            usecase_name_item, 
            priority_item, 
            user_request_item, # Data otomatis
            team_item,         # Data otomatis
            reason_item, 
            prompt_item
        )

        print("Exiting addPrompt function")
        return {"status": 200, "message": "Operation Successful!"}

     # --- MODIFIKASI FUNGSI INI ---
    async def getRequests(self, current_user: dict):
        print("Entering getRequests function")
        
        # Cek apakah pengguna adalah superadmin
        # Ganti SUPERADMIN_TEAM_ID dengan ID tim superadmin Anda yang sebenarnya
        SUPERADMIN_TEAM_ID = "8ea384d2-9d47-49d7-be95-b45d08a07aa3"
        team_id = current_user.get("id_team")
        is_super_admin = str(team_id) == SUPERADMIN_TEAM_ID
        
        team_to_filter = None
        if not is_super_admin:
            team_to_filter = current_user.get("team_name")

        requests = await self.repo.getRequestRepo(team_name=team_to_filter)

        print("Exiting getRequests function")
        return {"status": 200, "message": "Operation Successful!", "data": requests}
    
    async def getRequestsById(self, id: int):
        print("Entering getRquestsById function")

        request = await self.repo.getRequestByIdRepo(id=id)

        print("Exiting getRquestsById function")
        return {"status": 200, "message": "Operation Successfull!", "data": request}
    
    async def updatePrompt(self, id: int, data_to_update: dict):
        print("Entering updatePrompt function")
        
        # Langkah 1: Ambil data prompt saat ini dari database
        current_request = await self.repo.getRequestByIdRepo(id)
        if not current_request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        # Langkah 2: Tambahkan penjagaan status
        if current_request.get('status') in ['approved', 'rejected']:
            raise HTTPException(
                status_code=403, # 403 Forbidden
                detail=f"Cannot edit a prompt with status '{current_request.get('status')}'."
            )
            
        # Langkah 3: Jika status 'pending', lanjutkan proses update
        updated_request = await self.repo.updatePromptRepo(id, data_to_update)
        if not updated_request:
            # Ini seharusnya tidak terjadi jika pengecekan pertama lolos, tapi baik untuk keamanan
            raise HTTPException(status_code=404, detail="Request not found during update")

        return {"status": 200, "message": "Update successful!", "data": updated_request}

    # --- FUNGSI BARU ---
    async def deletePrompt(self, id: int):
        print("Entering deletePrompt function")
        success = await self.repo.deletePromptRepo(id)
        if not success:
            return {"status": 404, "message": "Request not found"}
        return {"status": 200, "message": "Request deleted successfully!"}

    # --- FUNGSI BARU ---
    async def approveRequest(self, id: int):
        print("Entering approveRequest function")
        approved_request = await self.repo.updateStatusRepo(id, "approved")
        if not approved_request:
            return {"status": 404, "message": "Request not found"}
        team_name = approved_request.get('team')
        if team_name:
            channel = f"prompt-updates-{team_name.replace(' ', '_')}" # Ganti spasi agar nama channel valid
            send_pusher_notification(
                channel=channel,
                event='status-changed',
                data={
                    'message': f"Prompt '{approved_request.get('usecase_name')}' has been approved.",
                    'prompt_id': id
                }
            )
        return {"status": 200, "message": "Request approved!", "data": approved_request}

    # --- FUNGSI BARU ---
    async def rejectRequest(self, id: int):
        print("Entering rejectRequest function")
        rejected_request = await self.repo.updateStatusRepo(id, "rejected")
        if not rejected_request:
            return {"status": 404, "message": "Request not found"}
        
        team_name = rejected_request.get('team')
        if team_name:
            channel = f"prompt-updates-{team_name.replace(' ', '_')}"
            send_pusher_notification(
                channel=channel,
                event='status-changed',
                data={
                    'message': f"Prompt '{rejected_request.get('usecase_name')}' has been rejected.",
                    'prompt_id': id
                }
            )
        return {"status": 200, "message": "Request rejected!", "data": rejected_request}
