import logging

import httpx

from core.config import settings

logger = logging.getLogger(__name__)


class WhatsAppService:
    def __init__(self):
        self.api_key = settings.WHATSAPP_API_KEY
        self.base_url = settings.WHATSAPP_URL
        self.headers = {
            "D360-API-Key": self.api_key,
            "Content-Type": "application/json",
        }

    # ── internal helpers ──────────────────────────────────────────────────────

    async def _send_text(self, phone: str, body: str) -> dict:
        """Send a plain-text WhatsApp message."""
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {"body": body},
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{self.base_url}/messages",
                json=payload,
                headers=self.headers,
            )
            resp.raise_for_status()
            return resp.json()

    async def _send_with_sms_fallback(self, phone: str, message: str) -> None:
        """
        Try WhatsApp first; fall back to Termii SMS on any failure.
        Errors are logged but never raised — notifications are best-effort.
        """
        try:
            await self._send_text(phone, message)
            return
        except Exception as wa_err:
            logger.warning("WhatsApp send failed for %s: %s — falling back to SMS", phone, wa_err)

        # SMS fallback via Termii
        try:
            from services.termii import termii_service  # local import avoids circular deps

            termii_payload = {
                "api_key": termii_service.api_key,
                "to": phone,
                "from": termii_service.sender_id,
                "sms": message,
                "type": "plain",
                "channel": "generic",
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    "https://api.ng.termii.com/api/sms/send",
                    json=termii_payload,
                )
                resp.raise_for_status()
        except Exception as sms_err:
            logger.error("SMS fallback also failed for %s: %s", phone, sms_err)

    # ── OTP (existing) ────────────────────────────────────────────────────────

    async def send_template_message(self, phone: str, template_name: str, components: list) -> dict:
        """Send a WhatsApp template message."""
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": "en_US"},
                "components": components,
            },
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{self.base_url}/messages",
                json=payload,
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    async def send_otp_message(self, phone: str, otp: str) -> dict:
        """Send OTP via WhatsApp."""
        components = [
            {
                "type": "body",
                "parameters": [{"type": "text", "text": otp}],
            }
        ]
        return await self.send_template_message(phone, "otp_template", components)

    # ── Agreement notifications ───────────────────────────────────────────────

    async def send_agreement_invite(
        self,
        phone: str,
        initiator_name: str,
        agreement_title: str,
        amount: str,
        confirm_url: str,
    ) -> None:
        """
        Notify the counterparty that they've been invited to an agreement.
        Falls back to SMS if WhatsApp fails.
        """
        message = (
            f"Hi, {initiator_name} has sent you an agreement on Settle.\n\n"
            f"*{agreement_title}*\n"
            f"Amount: ₦{amount}\n\n"
            f"Tap the link below to review and confirm:\n{confirm_url}\n\n"
            f"This link expires in 72 hours."
        )
        await self._send_with_sms_fallback(phone, message)

    async def send_sealed_confirmation(
        self,
        phone: str,
        agreement_title: str,
        amount: str,
        record_url: str,
    ) -> None:
        """
        Notify a party that the agreement has been sealed.
        Falls back to SMS if WhatsApp fails.
        """
        message = (
            f"Your agreement has been sealed on Settle.\n\n"
            f"*{agreement_title}*\n"
            f"Amount: ₦{amount}\n\n"
            f"Both parties have confirmed. This agreement is now active.\n"
            f"View your record here: {record_url}"
        )
        await self._send_with_sms_fallback(phone, message)

    async def send_payment_reminder(
        self,
        phone: str,
        agreement_title: str,
        amount_due: str,
        due_date: str,
    ) -> None:
        """
        Send a payment reminder to a party.
        Falls back to SMS if WhatsApp fails.
        """
        message = (
            f"Friendly reminder from Settle:\n\n"
            f"*{agreement_title}*\n"
            f"Amount due: ₦{amount_due}\n"
            f"Due date: {due_date}\n\n"
            f"Please make sure payment is sorted before the due date."
        )
        await self._send_with_sms_fallback(phone, message)


whatsapp_service = WhatsAppService()
