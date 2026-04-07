from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List


# Auth Schemas
class OTPRequest(BaseModel):
    phone: str = Field(..., pattern=r"^\+?234\d{10}$")


class OTPVerifyRequest(BaseModel):
    phone: str = Field(..., pattern=r"^\+?234\d{10}$")
    otp: str = Field(..., min_length=6, max_length=6)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    phone: str
    created_at: datetime


# Agreement Schemas
class AgreementCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    parties: List[str] = Field(..., min_items=2)
    amount: Optional[float] = Field(None, ge=0)
    due_date: Optional[datetime] = None


class AgreementResponse(BaseModel):
    id: str
    title: str
    description: str
    parties: List[str]
    amount: Optional[float]
    due_date: Optional[datetime]
    status: str
    created_by: str
    created_at: datetime


class AgreementConfirmRequest(BaseModel):
    token: str = Field(..., min_length=32)


class AgreementConfirmResponse(BaseModel):
    message: str
    agreement_id: str


# Payment Schemas
class PaymentInitiateRequest(BaseModel):
    agreement_id: str
    amount: float
    email: EmailStr


class PaymentInitiateResponse(BaseModel):
    reference: str
    authorization_url: str
    message: str


# Notification Schemas
class NotificationSendRequest(BaseModel):
    phone: str
    message: str
    channel: str = Field(..., pattern="^(sms|whatsapp)$")
