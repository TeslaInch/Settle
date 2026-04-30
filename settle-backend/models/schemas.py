from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, EmailStr, Field


# ── Auth ──────────────────────────────────────────────────────────────────────

class EmailRequest(BaseModel):
    email: EmailStr


class EmailVerifyRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    is_new_user: bool


class UserProfile(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None


# ── Agreements ────────────────────────────────────────────────────────────────

class AgreementCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    amount: float = Field(..., gt=0)
    terms: str = Field(..., min_length=1)
    counterparty_email: EmailStr
    repayment_date: datetime


class AgreementResponse(BaseModel):
    id: str
    title: str
    amount: float
    terms: str
    status: str
    initiator_id: str
    initiator_email: Optional[str] = None
    initiator_name: Optional[str] = None
    counterparty_id: Optional[str] = None
    counterparty_email: str
    counterparty_name: Optional[str] = None
    other_party_name: Optional[str] = None
    repayment_date: datetime
    seal_hash: Optional[str] = None
    seal_payload: Optional[Any] = None
    sealed_at: Optional[datetime] = None
    created_at: datetime


class ConfirmRequest(BaseModel):
    confirmation_token: str = Field(..., min_length=1)


class ConfirmResponse(BaseModel):
    message: str
    agreement: AgreementResponse


# ── Payments ──────────────────────────────────────────────────────────────────

class PaymentLogRequest(BaseModel):
    amount: float = Field(..., gt=0)
    note: Optional[str] = None


class PaymentResponse(BaseModel):
    id: str
    agreement_id: str
    payer_id: str
    amount: float
    note: Optional[str] = None
    logged_at: datetime
    confirmed_by_receiver: bool
    confirmed_at: Optional[datetime] = None


# ── Notifications ─────────────────────────────────────────────────────────────

class NotificationResponse(BaseModel):
    id: str
    user_id: str
    agreement_id: Optional[str] = None
    type: str
    channel: str
    status: str
    sent_at: datetime
