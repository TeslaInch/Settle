from fastapi import HTTPException
import httpx

from core.config import settings


class WhatsAppService:
    def __init__(self):
        self.api_key = settings.WHATSAPP_API_KEY
        self.base_url = settings.WHATSAPP_URL
        self.headers = {
            "D360-API-Key": self.api_key,
            "Content-Type": "application/json",
        }

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

        async with httpx.AsyncClient() as client:
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
                "parameters": [
                    {"type": "text", "text": otp},
                ],
            }
        ]
        return await self.send_template_message(phone, "otp_template", components)


whatsapp_service = WhatsAppService()
