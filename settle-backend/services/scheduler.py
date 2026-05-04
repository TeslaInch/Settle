import logging
from datetime import date, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def start_scheduler() -> None:
    """Register all jobs and start the scheduler."""
    scheduler.add_job(
        payment_reminders,
        CronTrigger(hour=8, minute=0, timezone="Africa/Lagos"),
        id="payment_reminders",
        replace_existing=True,
    )
    scheduler.add_job(
        mark_overdue,
        CronTrigger(hour=8, minute=0, timezone="Africa/Lagos"),
        id="mark_overdue",
        replace_existing=True,
    )
    if not scheduler.running:
        scheduler.start()
    logger.info("Scheduler started with jobs: payment_reminders, mark_overdue")


def stop_scheduler() -> None:
    """Shut down the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")


# ── Jobs ──────────────────────────────────────────────────────────────────────

def payment_reminders() -> None:
    """
    Daily at 08:00 Africa/Lagos.
    Find active agreements due in exactly 2 days and email both parties.
    """
    try:
        from core.database import supabase
        from core.config import settings
        from services.email import email_service
        import asyncio

        target_date = (date.today() + timedelta(days=2)).isoformat()

        result = (
            supabase.table("agreements")
            .select("*")
            .eq("status", "active")
            .eq("repayment_date", target_date)
            .execute()
        )

        agreements = result.data or []
        logger.info("payment_reminders: found %d agreements due on %s", len(agreements), target_date)

        for agreement in agreements:
            try:
                initiator_id = agreement["initiator_id"]
                counterparty_id = agreement.get("counterparty_id")

                initiator_result = (
                    supabase.table("profiles")
                    .select("id, email, full_name")
                    .eq("id", initiator_id)
                    .single()
                    .execute()
                )
                initiator = initiator_result.data

                counterparty = None
                if counterparty_id:
                    cp_result = (
                        supabase.table("profiles")
                        .select("id, email, full_name")
                        .eq("id", counterparty_id)
                        .single()
                        .execute()
                    )
                    counterparty = cp_result.data

                amount_str = f"{float(agreement['amount']):,.2f}"
                due_date_str = str(agreement["repayment_date"])
                agreement_url = f"{settings.FRONTEND_URL}/agreements/{agreement['id']}"

                for profile in [initiator, counterparty]:
                    if profile:
                        asyncio.run(
                            email_service.send_payment_reminder(
                                to_email=profile["email"],
                                to_name=profile.get("full_name") or profile["email"],
                                agreement_title=agreement["title"],
                                amount=amount_str,
                                currency_symbol="₦",
                                due_date=due_date_str,
                                agreement_url=agreement_url,
                            )
                        )
            except Exception as exc:
                logger.error("payment_reminders: error on agreement %s: %s", agreement.get("id"), exc)

    except Exception as exc:
        logger.error("payment_reminders job failed: %s", exc)


def mark_overdue() -> None:
    """
    Daily at 08:00 Africa/Lagos.
    Batch-update active agreements past their repayment_date to 'overdue'.
    """
    try:
        from core.database import supabase

        today = date.today().isoformat()

        result = (
            supabase.table("agreements")
            .update({"status": "overdue"})
            .eq("status", "active")
            .lt("repayment_date", today)
            .execute()
        )

        updated = len(result.data) if result.data else 0
        logger.info("mark_overdue: marked %d agreements as overdue", updated)

    except Exception as exc:
        logger.error("mark_overdue job failed: %s", exc)
