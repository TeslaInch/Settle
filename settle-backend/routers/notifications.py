from fastapi import APIRouter, Depends, HTTPException, status

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


@router.get("/unread-count", response_model=dict)
async def get_unread_count(
    current_user: UserProfile = Depends(get_current_user),
):
    """Return the count of unread notifications for the current user."""
    result = (
        supabase.table("notifications")
        .select("id", count="exact")
        .eq("user_id", current_user.id)
        .eq("read", False)
        .execute()
    )

    return {"count": result.count or 0}


@router.post("/{notification_id}/read", response_model=dict)
async def mark_notification_read(
    notification_id: str,
    current_user: UserProfile = Depends(get_current_user),
):
    """Mark a specific notification as read."""
    # First verify the notification belongs to the current user
    result = (
        supabase.table("notifications")
        .select("id")
        .eq("id", notification_id)
        .eq("user_id", current_user.id)
        .maybe_single()
        .execute()
    )

    if not result or not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found."
        )

    supabase.table("notifications").update({"read": True}).eq("id", notification_id).execute()

    return {"success": True}


@router.post("/read-all", response_model=dict)
async def mark_all_notifications_read(
    current_user: UserProfile = Depends(get_current_user),
):
    """Mark all notifications for the current user as read."""
    supabase.table("notifications").update({"read": True}).eq("user_id", current_user.id).execute()

    return {"success": True}
