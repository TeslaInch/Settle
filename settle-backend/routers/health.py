from fastapi import APIRouter

from services.whatsapp import whatsapp_service

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check():
    """Basic liveness check."""
    from core.config import settings
    return {"status": "healthy", "environment": settings.ENVIRONMENT}


@router.get("/whatsapp")
async def whatsapp_health():
    """
    Verify that the configured WhatsApp Cloud API credentials are live.
    Makes a read-only call to Meta — no message is sent.
    Use this after deployment to confirm WhatsApp connectivity.
    """
    ok, detail = await whatsapp_service.check_credentials()

    if ok:
        return {"status": "ok"}

    return {"status": "error", "detail": detail}
