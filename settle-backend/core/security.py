import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

from jose import jwt

from core.config import settings


def hash_otp(otp: str) -> str:
    """Hash OTP before storing to avoid storing raw values."""
    return hashlib.sha256(otp.encode()).hexdigest()


def verify_otp(hashed_otp: str, otp: str) -> bool:
    """Verify an OTP against its hash."""
    return hashlib.sha256(otp.encode()).hexdigest() == hashed_otp


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def generate_otp(length: int = 6) -> str:
    """Generate a random numeric OTP."""
    return secrets.token_hex(length // 2).zfill(length)[:length]


def generate_token() -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(32)
