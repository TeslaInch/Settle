from datetime import datetime, timezone

from core.database import supabase


class NotificationService:

    def create(
        self,
        user_id: str,
        agreement_id: str,
        type: str,
        message: str,
        channel: str = "in_app"
    ) -> None:
        try:
            supabase.table("notifications").insert({
                "user_id": user_id,
                "agreement_id": agreement_id,
                "type": type,
                "message": message,
                "channel": channel,
                "read": False,
                "sent_at": datetime.now(
                    timezone.utc
                ).isoformat()
            }).execute()
        except Exception:
            pass  # never crash main operation


notify_service = NotificationService()
