# src/notifications/handler.py
from .repository import NotificationRepository
from .schemas import NotificationCreate
from ..utils.pusher import send_pusher_notification
from uuid import UUID
from fastapi import HTTPException

class NotificationHandler:
    def __init__(self):
        self.repo = NotificationRepository()

    def create_and_dispatch(self, data: NotificationCreate, creator_id: UUID, creator_type: str = 'user'):
        if data.target_type in ['team', 'user'] and not data.target_id:
            raise HTTPException(status_code=400, detail="target_id is required for team or user notifications.")

        # Jika notifikasi dari sistem, creator_id bisa null
        if creator_type == 'system':
            creator_id = None

        notif_data = data.model_dump()
        new_notif = self.repo.create_notification(notif_data, creator_id, creator_type)
        
        target_user_ids = self.repo.get_target_user_ids(data.target_type, data.target_id)
        self.repo.link_notification_to_users(new_notif['id'], target_user_ids)

        for user_id in target_user_ids:
            channel_name = f"private-notifications-{user_id}"
            send_pusher_notification(
                channel=channel_name,
                event='new-notification',
                data={'title': data.title, 'message': data.message}
            )
        
        return {"status": "success", "message": f"Notification sent to {len(target_user_ids)} user(s)."}
        
    # UBAH FUNGSI INI
    def get_user_notifications(self, user_id: UUID, limit: int, offset: int):
        return self.repo.get_notifications_for_user(user_id, limit, offset)
        
        
    def mark_all_user_notifications_as_read(self, user_id: UUID):
        updated = self.repo.mark_all_as_read(user_id)
        return {"status": "success", "updated": updated}
    
    # Tambahkan fungsi ini di dalam kelas NotificationHandler
    def mark_one_notification_as_read(self, user_id: UUID, notification_id: UUID):
        updated = self.repo.mark_as_read(user_id, notification_id)
        return {"status": "success", "updated": updated}