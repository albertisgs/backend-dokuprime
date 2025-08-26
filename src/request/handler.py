import os
from dotenv import load_dotenv
from .repository import RequestRepository
from fastapi import HTTPException 
from src.utils.pusher import send_pusher_notification

from src.notifications.handler import NotificationHandler
from src.notifications.schemas import NotificationCreate
from src.usermanagement.repository import UserManagementRepository

class RequestHandler:
    def __init__(self):
        self.repo = RequestRepository()
        self.notification_handler = NotificationHandler() # 2. Inisialisasi handler notifikasi
        self.user_repo = UserManagementRepository() # 2. Inisialisasi repo user
        print("Handler Initiated")

     # --- MODIFIKASI FUNGSI INI ---
    async def addPrompt(self, new_request: dict, current_user: dict):
        # Ambil user_request dan team dari profil pengguna yang login, bukan dari input manual
        user_request_item = current_user.get("username", "Unknown User")
        team_item = current_user.get("team_name", "Unknown Team")
        creator_id = current_user.get("id")
        team_id = current_user.get("id_team")

        # Ambil data sisa dari payload
        usecase_name_item = new_request["usecase_name"]
        priority_item = new_request["priority"]
        reason_item = new_request["reason"]
        prompt_item = new_request["prompt"]

        # Kirim data yang sudah divalidasi ke repository
        await self.repo.addPromptRepo(
            usecase_name_item, 
            priority_item, 
            user_request_item, 
            team_item,         
            reason_item, 
            prompt_item,
            creator_id=creator_id
        )

        manager_ids = self.user_repo.get_manager_ids_by_team(team_id)
        for manager_id in manager_ids:
            # Pastikan tidak mengirim notifikasi ke diri sendiri jika pembuat adalah manajer
            if manager_id != creator_id:
                notif_data = NotificationCreate(
                    title="New Prompt Submitted",
                    message=f"Prompt '{new_request['usecase_name']}' was submitted by {user_request_item}.",
                    target_type='user',
                    target_id=manager_id,
                    link_to="/prompt-management"
                )
                self.notification_handler.create_and_dispatch(notif_data, creator_id=creator_id)

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
    async def approveRequest(self, id: int, current_user: dict):
        print("Entering approveRequest function")
        approved_request = await self.repo.updateStatusRepo(id, "approved")
        if not approved_request:
            raise HTTPException(status_code=404, detail="Request not found")

        requester_id = approved_request.get('creator_id')
        manager_id = current_user.get("id")

        # 4. Kirim notifikasi ke pembuat permintaan
        if requester_id and requester_id != manager_id:
            notif_data = NotificationCreate(
                title="Prompt Approved",
                message=f"Your prompt '{approved_request.get('usecase_name')}' has been approved.",
                target_type='user',
                target_id=requester_id,
                link_to="/prompt-management"
            )
            # Notifikasi dibuat oleh manager yang melakukan aksi
            self.notification_handler.create_and_dispatch(notif_data, creator_id=manager_id)
            
       
        return {"status": 200, "message": "Request approved!", "data": approved_request}

    # --- FUNGSI BARU ---
    async def rejectRequest(self, id: int, current_user: dict):
        print("Entering rejectRequest function")
        rejected_request = await self.repo.updateStatusRepo(id, "rejected")
        if not rejected_request:
            raise HTTPException(status_code=404, detail="Request not found")

        requester_id = rejected_request.get('creator_id')
        manager_id = current_user.get("id")
        
        # 5. Kirim notifikasi ke pembuat permintaan
        if requester_id and requester_id != manager_id:
            notif_data = NotificationCreate(
                title="Prompt Rejected",
                message=f"Your prompt '{rejected_request.get('usecase_name')}' has been rejected.",
                target_type='user',
                target_id=requester_id,
                link_to="/prompt-management"
            )
            self.notification_handler.create_and_dispatch(notif_data, creator_id=manager_id)

        
        return {"status": 200, "message": "Request rejected!", "data": rejected_request}
