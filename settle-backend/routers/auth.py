# ─────────────────────────────────────────────────────────────────────────────
# OTP PROVIDER: Supabase Auth (Twilio)
#
# When Termii business verification is complete,
# replace supabase.auth OTP calls with TermiiService
# for +234 numbers only. All other numbers stay on Twilio.
#
# Config switch: settings.USE_TERMII_FOR_NG = True/False
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import APIRouter, HTTPException, status

from core.database import supabase
from core.security import create_access_token
from models.schemas import OTPVerifyRequest, PhoneRequest, TokenResponse

router = APIRouter()


@router.post("/send-otp")
async def send_otp(body: PhoneRequest) -> dict:
    """
    Send a 6-digit OTP to the given phone number via Supabase Auth (Twilio).
    Phone number is normalized to +234 format by PhoneRequest validation.
    """
    try:
        response = supabase.auth.sign_in_with_otp({"phone": body.phone_number})
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to send OTP: {str(exc)}",
        )

    # Supabase returns an AuthOtpResponse; an error surfaces as an exception
    # in the Python client, but guard against unexpected None responses too.
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to send OTP. Please try again.",
        )

    return {
        "message": "OTP sent successfully.",
        "phone_number": body.phone_number,
    }


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(body: OTPVerifyRequest) -> TokenResponse:
    """
    Verify the OTP code via Supabase Auth.
    - New users: full_name is required to create their profile.
    - Existing users: full_name is ignored.
    Returns a JWT access token and an is_new_user flag.
    """
    # 1. Verify OTP with Supabase Auth (Twilio under the hood)
    try:
        auth_response = supabase.auth.verify_otp({
            "phone": body.phone_number,
            "token": body.otp_code,
            "type": "sms",
        })
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired code.",
        )

    if not auth_response or not auth_response.user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired code.",
        )

    auth_user = auth_response.user
    user_id = auth_user.id

    # 2. Check if a profile already exists
    existing = (
        supabase.table("profiles")
        .select("id, phone_number, full_name")
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )

    is_new_user = existing.data is None

    if is_new_user:
        # full_name is required for new users
        if not body.full_name or not body.full_name.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="full_name is required for new users.",
            )

        # Insert profile row
        # The DB trigger (handle_new_user) may have already created a minimal row;
        # upsert ensures we always set full_name correctly.
        profile_result = (
            supabase.table("profiles")
            .upsert({
                "id": user_id,
                "phone_number": body.phone_number,
                "full_name": body.full_name.strip(),
            })
            .execute()
        )

        if not profile_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user profile. Please try again.",
            )

    # 3. Issue our own JWT (we manage sessions independently of Supabase Auth)
    access_token = create_access_token(data={"sub": user_id})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        is_new_user=is_new_user,
    )
