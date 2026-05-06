from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from core.config import settings
from routers import auth, agreements, payments, notifications, health
from services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="Settle API",
    description="Nigerian informal agreement witness API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        settings.FRONTEND_URL,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CORS preflight handler (must be before routers)
@app.options("/{rest_of_path:path}")
async def preflight_handler(
    rest_of_path: str,
    request: Request
) -> Response:
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin":
                request.headers.get("origin", "*"),
            "Access-Control-Allow-Methods":
                "GET, POST, PUT, PATCH, DELETE, OPTIONS",
            "Access-Control-Allow-Headers":
                "Authorization, Content-Type",
            "Access-Control-Allow-Credentials": "true",
        }
    )

# Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(agreements.router, prefix="/api/v1", tags=["agreements"])
app.include_router(payments.router, prefix="/api/v1", tags=["payments"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(health.router, prefix="/api/v1", tags=["health"])
