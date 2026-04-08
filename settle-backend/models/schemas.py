import re
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator


# ── helpers ──────────────────────────────────────────────────────────────────

def normalize_nigerian_phone(value: str) -> str:
    """
    Accept:
      +2348012345678  (13 chars with country code)
       2348012345678  (13 chars, no +)
       08012345678    (11 chars, local 0-prefix)
    Return: +2348012345678
    """
    v = value.strip().replace(" ", "").replace("-", "")

    if v.startswith("+234") and len(v) == 14 and v[4:].isdigit():
        return v

    if v.startswith("234") and len(v) == 13 and v[3:].isdigit():
        return f"+{v}"

    if v.startswith("0") and len(v) == 11 and v[1:].isdigit():
        return f"+234{v[1:]}"

    raise ValueError(
        "Invalid Nigerian phone number. "
        "Use +2348XXXXXXXXX, 2348XXXXXXXXX, or 08XXXXXXXXX format."
    )


# ── Auth ─────────────────────────────────────────────────────────────────────

class PhoneRequest(BaseModel):
    phone_number: str

    @field_validator("phone_number")
    @classmethod
    def validate_and_normalize(cls, v: str) -> str:
        return normalize_nigerian_phone(v)


class OTPVerifyRequest(BaseModel):
    phone_number: str
    otp_code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")
    pin_id: str = Field(..., min_length=1, description="pinId returned by /send-otp")
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)

    @field_validator("phone_number")
    @classmethod
    def validate_and_normalize(cls, v: str) -> str:
        return normalize_nigerian_phone(v)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    is_new_user: bool


class UserProfile(BaseModel):
    id: str
    phone_number: str
    full_name: Optional[str] = None


# ── Agreements ────────────────────────────────────────────────────────────────

class AgreementCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    amount: float = Field(..., gt=0)
    terms: str = Field(..., min_length=1)
    counterparty_phone: str
    repayment_date: datetime

    @field_validator("counterparty_phone")
    @classmethod
    def validate_counterparty_phone(cls, v: str) -> str:
        return normalize_nigerian_phone(v)


class AgreementResponse(BaseModel):
    id: str
    title: str
    amount: float
    terms: str
    initiator_id: str
    counterparty_id: Optional[str] = None
    counterparty_phone: str
    repayment_date: datetime
    status: str
    seal_hash: Optional[str] = None
    sealed_at: Optional[datetime] = None
    created_at: datetime


class AgreementConfirmRequest(BaseModel):
    token: str = Field(..., min_length=32)


class AgreementConfirmResponse(BaseModel):
    message: str
    agreement_id: str


# ── Payments ──────────────────────────────────────────────────────────────────

class PaymentLogRequest(BaseModel):
    agreement_id: str
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

class NotificationSendRequest(BaseModel):
    phone: str
    message: str
    channel: str = Field(..., pattern="^(sms|whatsapp)$")
