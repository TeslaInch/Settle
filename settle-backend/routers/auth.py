from fastapi import APIRouter, HTTPException, status

from core.database import supabase
from core.security import create_access_token
from models.schemas import OTPVerifyRequest, PhoneRequest, TokenResponse
from services.termii import termii_service

router = APIRouter()


@router.post("/send-otp")
async def send_otp(body: PhoneRequest) -> dict:
    """
    Send a 6-digit OTP to the given Nigerian phone number via Termii.
    Phone number is normalized to +234 format before sending.
    Returns the pinId from Termii — the client must pass this back on verify.
    """
    termii_response = await termii_service.send_otp(body.phone_number)

    return {
        "message": "OTP sent successfully.",
        "phone_number": body.phone_number,
        "pin_id": termii_response["pinId"],
    }


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(body: OTPVerifyRequest) -> TokenResponse:
    """
    Verify the OTP code against Termii.
    - If the user is new, full_name is required to create their profile.
    - If the user exists, full_name is ignored.
    Returns a JWT access token and an is_new_user flag.
    """
    # 1. Verify OTP with Termii
    # pin_id must be supplied by the client (returned from /send-otp)
    # We re-use otp_code as the pin; pin_id comes from the request body
    # Note: we embed pin_id in the verify request — see OTPVerifyRequest
    await termii_service.verify_otp(body.pin_id, body.otp_code)

    # 2. Check if profile already exists
    existing = (
        supabase.table("profiles")
        .select("id, phone_number, full_name")
        .eq("phone_number", body.phone_number)
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

        # Create Supabase Auth user with phone
        auth_response = supabase.auth.admin.create_user({
            "phone": body.phone_number,
            "phone_confirm": True,
            "user_metadata": {"full_name": body.full_name.strip()},
        })

        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user account. Please try again.",
            )

        user_id = auth_response.user.id

        # Insert profile row (trigger may also do this, but we set full_name here)
        profile_insert = (
            supabase.table("profiles")
            .upsert({
                "id": user_id,
                "phone_number": body.phone_number,
                "full_name": body.full_name.strip(),
            })
            .execute()
        )

        if not profile_insert.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user profile. Please try again.",
            )

    else:
        user_id = existing.data["id"]

    # 3. Issue JWT
    access_token = create_access_token(data={"sub": user_id})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        is_new_user=is_new_user,
    )
