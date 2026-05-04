from fastapi import APIRouter

from core.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check():
    """Basic liveness check."""
    return {"status": "healthy", "environment": settings.ENVIRONMENT}
