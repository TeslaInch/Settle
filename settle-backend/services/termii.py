from fastapi import HTTPException
import httpx

from core.config import settings


class TermiiService:
    def __init__(self):
        self.api_key = settings.TERMII_API_KEY
        self.sender_id = settings.TERMII_SENDER_ID
        self.base_url = "https://termii.com/api/sms/send"

    async def send_otp(self, phone: str, otp: str) -> dict:
        """Send OTP via Termii SMS."""
        payload = {
            "api_key": self.api_key,
            "to": phone,
            "from": self.sender_id,
            "sms": f"Your Settle OTP is: {otp}. Do not share this code.",
            "type": "text",
            "channel": "generic",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.base_url, json=payload)
            response.raise_for_status()
            return response.json()

    async def send_whatsapp_otp(self, phone: str, otp: str) -> dict:
        """Send OTP via WhatsApp using 360Dialog."""
        # This will be implemented when WhatsApp integration is added
        raise NotImplementedError("WhatsApp OTP not yet implemented")


termii_service = TermiiService()
