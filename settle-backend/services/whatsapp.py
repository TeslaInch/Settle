import logging
from datetime import datetime, timezone

import httpx

from core.config import settings

logger = logging.getLogger(__name__)

# Max characters Meta allows in a plain-text WhatsApp message body
_MAX_CHARS = 1024


def _truncate(text: str) -> str:
    """Hard-truncate to Meta's 1024-char limit."""
    return text[:_MAX_CHARS]


class WhatsAppService:
    """
    Async WhatsApp client using Meta's WhatsApp Cloud API.
    All public methods return bool — True on success, False on any failure.
    Failures are logged but never raised; the caller must never crash because
    a notification failed.
    """

    def __init__(self) -> None:
        self._url = settings.WHATSAPP_BASE_URL
        self._headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }

    # ── private ───────────────────────────────────────────────────────────────

    async def _send_message(self, to: str, message: str) -> bool:
        """
        Send a plain-text WhatsApp message via Meta Cloud API.
        Returns True on HTTP 200, False on any error.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": _truncate(message),
            },
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    self._url,
                    json=payload,
                    headers=self._headers,
                )

            if resp.status_code == 200:
                return True

            logger.error(
                "WhatsApp send failed | to=%s | status=%s | body=%s",
                to,
                resp.status_code,
                resp.text[:300],
            )
            self._log_failure(to, message, f"HTTP {resp.status_code}: {resp.text[:200]}")
            return False

        except httpx.TimeoutException:
            logger.error("WhatsApp send timed out | to=%s", to)
            self._log_failure(to, message, "Request timed out")
            return False
        except Exception as exc:
            logger.error("WhatsApp send error | to=%s | error=%s", to, exc)
            self._log_failure(to, message, str(exc))
            return False

    def _log_failure(self, phone: str, message: str, reason: str) -> None:
        """
        Best-effort write to the notifications table so failures are traceable.
        Swallows any DB error — logging must never crash the app.
        """
        try:
            from core.database import supabase  # local import avoids circular deps

            supabase.table("notifications").insert({
                "user_id": None,
                "type": "whatsapp",
                "channel": "whatsapp",
                "status": "failed",
                "sent_at": datetime.now(timezone.utc).isoformat(),
            }).execute()
        except Exception as db_exc:
            logger.warning("Could not log WhatsApp failure to DB: %s", db_exc)

    # ── health check ──────────────────────────────────────────────────────────

    async def check_credentials(self) -> tuple[bool, str]:
        """
        Verify that the configured credentials are accepted by Meta.
        Calls the phone number endpoint (read-only, no message sent).
        Returns (True, "") on success or (False, error_detail) on failure.
        """
        url = (
            f"https://graph.facebook.com"
            f"/{settings.WHATSAPP_API_VERSION}"
            f"/{settings.WHATSAPP_PHONE_NUMBER_ID}"
        )
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"},
                )
            if resp.status_code == 200:
                return True, ""
            return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
        except Exception as exc:
            return False, str(exc)

    # ── public notification methods ───────────────────────────────────────────

    async def send_agreement_invite(
        self,
        counterparty_phone: str,
        initiator_name: str,
        agreement_title: str,
        amount: str,
        currency_symbol: str,
        repayment_date: str,
        confirm_url: str,
    ) -> bool:
        message = (
            f"Hi! {initiator_name} has created an agreement with you on Settle.\n\n"
            f"\U0001f4cb {agreement_title}\n"
            f"\U0001f4b0 Amount: {currency_symbol}{amount}\n"
            f"\U0001f4c5 Repayment date: {repayment_date}\n\n"
            f"Tap the link to review and confirm:\n{confirm_url}\n\n"
            f"This link expires in 72 hours."
        )
        return await self._send_message(counterparty_phone, message)

    async def send_sealed_confirmation(
        self,
        phone: str,
        party_name: str,
        agreement_title: str,
        amount: str,
        currency_symbol: str,
        sealed_at: str,
        record_url: str,
    ) -> bool:
        message = (
            f"\u2705 Agreement Sealed\n\n"
            f"{agreement_title}\n"
            f"\U0001f4b0 {currency_symbol}{amount}\n"
            f"\U0001f512 Sealed: {sealed_at}\n\n"
            f"Both parties have confirmed. This agreement is now permanently "
            f"recorded and protected.\n\n"
            f"View your record: {record_url}"
        )
        return await self._send_message(phone, message)

    async def send_payment_logged(
        self,
        receiver_phone: str,
        payer_name: str,
        amount: str,
        currency_symbol: str,
        agreement_title: str,
        confirm_url: str,
    ) -> bool:
        message = (
            f"\U0001f4b0 Payment Logged\n\n"
            f"{payer_name} has recorded a payment of {currency_symbol}{amount} "
            f"against '{agreement_title}'.\n\n"
            f"Please confirm you received this payment:\n{confirm_url}"
        )
        return await self._send_message(receiver_phone, message)

    async def send_payment_confirmed(
        self,
        payer_phone: str,
        receiver_name: str,
        amount: str,
        currency_symbol: str,
        agreement_title: str,
    ) -> bool:
        message = (
            f"\u2705 Payment Confirmed\n\n"
            f"{receiver_name} has confirmed receipt of {currency_symbol}{amount} "
            f"for '{agreement_title}'.\n\n"
            f"Your payment record has been updated."
        )
        return await self._send_message(payer_phone, message)

    async def send_payment_reminder(
        self,
        phone: str,
        debtor_name: str,
        agreement_title: str,
        amount_due: str,
        currency_symbol: str,
        due_date: str,
        agreement_url: str,
    ) -> bool:
        message = (
            f"\u23f0 Payment Reminder\n\n"
            f"Hi {debtor_name}, your agreement '{agreement_title}' is due in 2 days.\n"
            f"Amount due: {currency_symbol}{amount_due}\n"
            f"Due date: {due_date}\n\n"
            f"View agreement: {agreement_url}"
        )
        return await self._send_message(phone, message)

    async def send_agreement_completed(
        self,
        phone: str,
        party_name: str,
        agreement_title: str,
        total_amount: str,
        currency_symbol: str,
    ) -> bool:
        message = (
            f"\U0001f389 Agreement Completed\n\n"
            f"'{agreement_title}' has been fully settled.\n"
            f"Total paid: {currency_symbol}{total_amount}\n\n"
            f"Great job \u2014 your Settle record is permanently saved."
        )
        return await self._send_message(phone, message)


whatsapp_service = WhatsAppService()
