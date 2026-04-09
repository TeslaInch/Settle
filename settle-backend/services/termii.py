import httpx
from fastapi import HTTPException, status

from core.config import settings

TERMII_SEND_OTP_URL   = "https://api.ng.termii.com/api/sms/otp/send"
TERMII_VERIFY_OTP_URL = "https://api.ng.termii.com/api/sms/otp/verify"


class TermiiService:
    def __init__(self):
        self.api_key   = settings.TERMII_API_KEY
        self.sender_id = settings.TERMII_SENDER_ID

    async def send_otp(self, phone_number: str) -> dict:
        """
        Send a 6-digit numeric OTP via Termii.
        Returns the raw Termii response dict.
        """
        payload = {
            "api_key":    self.api_key,
            "message_type": "NUMERIC",
            "to":         phone_number,
            "from":       self.sender_id,
            "channel":    "generic",
            "pin_attempts": 3,
            "pin_time_to_live": 5,   # minutes
            "pin_length":  6,
            "pin_placeholder": "< 1234 >",
            "message_text": "Your Settle verification code is < 1234 >. Valid for 5 minutes. Do not share.",
            "pin_type":   "NUMERIC",
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.post(TERMII_SEND_OTP_URL, json=payload)
            except httpx.TimeoutException:
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="OTP service timed out. Please try again.",
                )
            except httpx.RequestError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Could not reach OTP service: {str(exc)}",
                )

        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"OTP service returned an error: {resp.text}",
            )

        data = resp.json()

        # Termii returns a "pinId" on success
        if "pinId" not in data:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="OTP service did not return a pin ID. Please try again.",
            )

        return data

    async def verify_otp(self, pin_id: str, otp_code: str) -> dict:
        """
        Verify an OTP against Termii using the pinId returned by send_otp.
        Returns the raw Termii response dict.
        Raises HTTPException if verification fails.
        """
        payload = {
            "api_key": self.api_key,
            "pin_id":  pin_id,
            "pin":     otp_code,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.post(TERMII_VERIFY_OTP_URL, json=payload)
            except httpx.TimeoutException:
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="OTP verification service timed out. Please try again.",
                )
            except httpx.RequestError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Could not reach OTP verification service: {str(exc)}",
                )

        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"OTP verification service returned an error: {resp.text}",
            )

        data = resp.json()

        # Termii returns "verified": "True" on success
        if str(data.get("verified", "")).lower() != "true":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP. Please request a new code.",
            )

        return data


termii_service = TermiiService()
