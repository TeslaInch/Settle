from fastapi import APIRouter, Depends

from core.database import supabase
from core.security import get_current_user
from models.schemas import NotificationResponse, UserProfile

router = APIRouter()


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    current_user: UserProfile = Depends(get_current_user),
):
    """Return the last 20 notifications for the current user, newest first."""
    result = (
        supabase.table("notifications")
        .select("*")
        .eq("user_id", current_user.id)
        .order("sent_at", desc=True)
        .limit(20)
        .execute()
    )

    return result.data or []
