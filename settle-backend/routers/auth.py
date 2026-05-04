import random
import string
from datetime import datetime, timezone, timedelta

import resend
from fastapi import APIRouter, Depends, HTTPException, status

from core.config import settings
from core.database import supabase
from core.security import create_access_token, get_current_user
from models.schemas import EmailRequest, EmailVerifyRequest, TokenResponse, UserProfile

resend.api_key = settings.RESEND_API_KEY

router = APIRouter()


def _generate_otp() -> str:
    """Return a random 6-digit numeric string."""
    return "".join(random.choices(string.digits, k=6))


# ── POST /api/v1/auth/send-code ───────────────────────────────────────────────

@router.post("/send-code")
async def send_code(body: EmailRequest) -> dict:
    """
    Generate a 6-digit OTP, store it in otp_codes, and email it via Resend.
    Any previous unused codes for this email are deleted first.
    """
    email = body.email
    otp = _generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    # Delete any existing unused codes for this email
    supabase.table("otp_codes").delete().eq("email", email).eq("used", False).execute()

    # Insert new code
    insert_result = supabase.table("otp_codes").insert({
        "email": email,
        "code": otp,
        "expires_at": expires_at.isoformat(),
        "used": False,
    }).execute()

    if not insert_result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate code. Please try again.",
        )

    # Send email via Resend
    try:
        resend.Emails.send({
            "from": settings.FROM_EMAIL,
            "to": email,
            "subject": "Your Settle verification code",
            "html": f"""
<div style="font-family: sans-serif; max-width: 400px; margin: 0 auto; padding: 40px 20px;">
  <h2 style="color: #1B4332; margin: 0 0 8px;">Settle</h2>
  <p style="color: #374151; margin: 0 0 24px;">Your verification code is:</p>
  <div style="font-size: 48px; font-weight: bold; letter-spacing: 8px;
              color: #1B4332; padding: 20px 0; text-align: center;">
    {otp}
  </div>
  <p style="color: #6B7280; font-size: 14px; margin-top: 24px;">
    This code expires in 10 minutes.<br/>
    Do not share it with anyone.
  </p>
</div>
""",
        })
    except Exception as exc:
        print(f"RESEND ERROR: {exc}")
        # Clean up the stored code so the user can retry cleanly
        supabase.table("otp_codes").delete().eq("email", email).eq("used", False).execute()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send code. Please try again.",
        )

    return {"message": "Check your email for a 6-digit code."}


# ── POST /api/v1/auth/verify-code ─────────────────────────────────────────────

@router.post("/verify-code", response_model=TokenResponse)
async def verify_code(body: EmailVerifyRequest) -> TokenResponse:
    """
    Verify the submitted OTP against otp_codes.
    Creates a profile for new users, then issues a JWT.
    """
    email = body.email
    now_iso = datetime.now(timezone.utc).isoformat()

    # Fetch the most recent valid code for this email
    result = (
        supabase.table("otp_codes")
        .select("*")
        .eq("email", email)
        .eq("used", False)
        .gt("expires_at", now_iso)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired code.",
        )

    record = result.data[0]

    if record["code"] != body.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired code.",
        )

    # Mark code as used
    supabase.table("otp_codes").update({"used": True}).eq("id", record["id"]).execute()

    # Check if a profile already exists for this email
    try:
        profile_result = (
            supabase.table("profiles")
            .select("id, email, full_name")
            .eq("email", email)
            .maybe_single()
            .execute()
        )
        profile_data = profile_result.data if profile_result else None
    except Exception:
        profile_data = None

    is_new_user = profile_data is None

    if is_new_user:
        if not body.full_name or not body.full_name.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="full_name is required for new users.",
            )

        new_profile = (
            supabase.table("profiles")
            .insert({
                "email": email,
                "full_name": body.full_name.strip(),
            })
            .execute()
        )

        if not new_profile.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user profile. Please try again.",
            )

        profile_id = new_profile.data[0]["id"]
    else:
        profile_id = profile_data["id"]

    # Issue JWT
    access_token = create_access_token(data={"sub": str(profile_id)})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        is_new_user=is_new_user,
    )


# ── GET /api/v1/auth/me ───────────────────────────────────────────────────────

@router.get("/me", response_model=UserProfile)
async def get_me(current_user: UserProfile = Depends(get_current_user)) -> UserProfile:
    """Return the current authenticated user's profile."""
    return current_user
