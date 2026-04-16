from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from routers import auth, agreements, payments, notifications

app = FastAPI(
    title="Settle API",
    description="Nigerian informal agreement witness API",
    version="0.1.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        settings.PRODUCTION_FRONTEND_URL,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(agreements.router, prefix="/api/v1/agreements", tags=["agreements"])
# Payment routes live under both /agreements/{id}/payments and /payments/{id}/confirm
app.include_router(payments.router, prefix="/api/v1", tags=["payments"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "environment": settings.ENVIRONMENT}
