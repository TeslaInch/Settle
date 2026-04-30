# ─────────────────────────────────────────────────────────────────────────────
# AUTH PROVIDER: Supabase Auth (email OTP)
# Supabase sends a 6-digit code to the user's email address.
# We verify it, create a profile if new, then issue our own JWT.
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import APIRouter, Depends, HTTPException, status

from core.database import supabase
from core.security import create_access_token, get_current_user
from models.schemas import EmailRequest, EmailVerifyRequest, TokenResponse, UserProfile

router = APIRouter()


@router.post("/send-code")
async def send_code(body: EmailRequest) -> dict:
    """
    Send a 6-digit OTP to the given email address via Supabase Auth.
    """
    try:
        response = supabase.auth.sign_in_with_otp({"email": body.email})
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to send code: {str(exc)}",
        )

    if response is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to send code. Please try again.",
        )

    return {"message": "Check your email for a 6-digit code."}


@router.post("/verify-code", response_model=TokenResponse)
async def verify_code(body: EmailVerifyRequest) -> TokenResponse:
    """
    Verify the 6-digit email OTP via Supabase Auth.
    - New users: full_name is required to create their profile.
    - Existing users: full_name is ignored.
    Returns a JWT access token and an is_new_user flag.
    """
    # 1. Verify OTP with Supabase Auth
    try:
        auth_response = supabase.auth.verify_otp({
            "email": body.email,
            "token": body.code,
            "type": "email",
        })
    except Exception:
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
        .select("id, email, full_name")
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

        profile_result = (
            supabase.table("profiles")
            .upsert({
                "id": user_id,
                "email": body.email,
                "full_name": body.full_name.strip(),
            })
            .execute()
        )

        if not profile_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user profile. Please try again.",
            )

    # 3. Issue our own JWT
    access_token = create_access_token(data={"sub": user_id})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        is_new_user=is_new_user,
    )


@router.get("/me", response_model=UserProfile)
async def get_me(current_user: UserProfile = Depends(get_current_user)) -> UserProfile:
    """Return the current authenticated user's profile."""
    return current_user
