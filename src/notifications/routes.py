# src/notifications/routes.py
from fastapi import APIRouter, Depends
from .handler import NotificationHandler
from .schemas import NotificationCreate, NotificationListResponse
from ..utils.sessiondependencies import get_current_user_profile
from ..utils.dependecies import require_permission # Atau superadmin, sesuai kebutuhan
from uuid import UUID
# Untuk sementara, kita asumsikan hanya superadmin yang bisa mengirim notifikasi
from ..utils.dependecies import get_current_superadmin
from fastapi import Query

# Router untuk user yang login
router = APIRouter(
    tags=["Notifications"],
    dependencies=[Depends(get_current_user_profile)]
)

# Router khusus admin untuk mengirim notifikasi
admin_router = APIRouter(
    tags=["Notifications (Admin)"],
    dependencies=[Depends(get_current_superadmin)] # Lindungi endpoint ini
)

handler = NotificationHandler()

# Endpoint untuk user mendapatkan notifikasi mereka
@router.get("/", response_model=NotificationListResponse)
def get_my_notifications(
    current_user: dict = Depends(get_current_user_profile),
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0)
):
    user_id = current_user.get("id")
    return handler.get_user_notifications(user_id, limit, offset)

# Endpoint untuk user menandai semua notifikasi sebagai "dibaca"
@router.post("/read-all", status_code=200)
def mark_all_as_read(current_user: dict = Depends(get_current_user_profile)):
    user_id = current_user.get("id")
    return handler.mark_all_user_notifications_as_read(user_id)

# Tambahkan endpoint baru ini di dalam router
@router.post("/{notification_id}/read", status_code=200)
def mark_one_as_read(
    notification_id: UUID,
    current_user: dict = Depends(get_current_user_profile)
):
    user_id = current_user.get("id")
    return handler.mark_one_notification_as_read(user_id, notification_id)

# Endpoint untuk admin mengirim notifikasi baru
@admin_router.post("/")
def send_notification(data: NotificationCreate, current_user: dict = Depends(get_current_user_profile)):
    creator_id = current_user.get("id")
    return handler.create_and_dispatch(data, creator_id)

@admin_router.post("/system")
def send_system_notification(data: NotificationCreate):
    # Untuk notifikasi sistem, kita tidak memerlukan ID pembuat
    return handler.create_and_dispatch(data, creator_id=None, creator_type='system')

