from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from core.database import supabase
from core.security import get_current_user
from core.config import settings
from models.schemas import PaymentLogRequest, PaymentResponse, UserProfile
from services.email import email_service

router = APIRouter()


# ── helpers ───────────────────────────────────────────────────────────────────

def _is_party_to_agreement(agreement: dict, user_id: str) -> bool:
    return agreement["initiator_id"] == user_id or agreement.get("counterparty_id") == user_id


def _build_payment_response(row: dict) -> PaymentResponse:
    return PaymentResponse(
        id=row["id"],
        agreement_id=row["agreement_id"],
        payer_id=row["payer_id"],
        amount=float(row["amount"]),
        note=row.get("note"),
        logged_at=row["logged_at"],
        confirmed_by_receiver=row["confirmed_by_receiver"],
        confirmed_at=row.get("confirmed_at"),
    )


def _get_profile_by_id(user_id: str) -> dict | None:
    result = (
        supabase.table("profiles")
        .select("id, email, full_name")
        .eq("id", user_id)
        .single()
        .execute()
    )
    return result.data


def _format_amount(amount: float) -> str:
    return f"{amount:,.2f}"


# ── GET /agreements/{id}/payments ─────────────────────────────────────────────

@router.get("/agreements/{agreement_id}/payments", response_model=list[PaymentResponse])
async def list_payments(
    agreement_id: str,
    current_user: UserProfile = Depends(get_current_user),
):
    ag_result = (
        supabase.table("agreements")
        .select("*")
        .eq("id", agreement_id)
        .single()
        .execute()
    )

    if not ag_result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agreement not found.")

    agreement = ag_result.data

    if not _is_party_to_agreement(agreement, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a party to this agreement.",
        )

    pm_result = (
        supabase.table("payments")
        .select("*")
        .eq("agreement_id", agreement_id)
        .order("logged_at", desc=True)
        .execute()
    )

    return [_build_payment_response(r) for r in (pm_result.data or [])]


# ── POST /agreements/{id}/payments ────────────────────────────────────────────

@router.post(
    "/agreements/{agreement_id}/payments",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def log_payment(
    agreement_id: str,
    body: PaymentLogRequest,
    current_user: UserProfile = Depends(get_current_user),
):
    ag_result = (
        supabase.table("agreements")
        .select("*")
        .eq("id", agreement_id)
        .single()
        .execute()
    )

    if not ag_result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agreement not found.")

    agreement = ag_result.data

    if not _is_party_to_agreement(agreement, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a party to this agreement.",
        )

    if agreement["status"] != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot log payment on {agreement['status']} agreement.",
        )

    # Calculate remaining balance
    pm_result = (
        supabase.table("payments")
        .select("amount, confirmed_by_receiver")
        .eq("agreement_id", agreement_id)
        .execute()
    )

    total_paid = sum(
        float(p["amount"])
        for p in (pm_result.data or [])
        if p["confirmed_by_receiver"]
    )

    remaining = float(agreement["amount"]) - total_paid

    if body.amount > remaining:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment amount (₦{body.amount:,.2f}) exceeds remaining balance (₦{remaining:,.2f}).",
        )

    insert_data = {
        "agreement_id": agreement_id,
        "payer_id": current_user.id,
        "amount": body.amount,
        "note": body.note,
        "logged_at": datetime.now(timezone.utc).isoformat(),
        "confirmed_by_receiver": False,
    }

    result = supabase.table("payments").insert(insert_data).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to log payment.",
        )

    payment = result.data[0]

    # Notify receiver — best effort
    try:
        # Determine receiver: the party who is NOT the payer
        is_initiator = agreement["initiator_id"] == current_user.id
        receiver_id = agreement.get("counterparty_id") if is_initiator else agreement["initiator_id"]

        if receiver_id:
            receiver = _get_profile_by_id(receiver_id)
            if receiver:
                payer_name = current_user.full_name or current_user.email
                confirm_url = f"{settings.FRONTEND_URL}/payments/{agreement_id}"

                await email_service.send_payment_logged(
                    to_email=receiver["email"],
                    to_name=receiver.get("full_name") or receiver["email"],
                    payer_name=payer_name,
                    amount=_format_amount(body.amount),
                    currency_symbol="₦",
                    agreement_title=agreement["title"],
                    confirm_url=confirm_url,
                )
    except Exception:
        pass

    return _build_payment_response(payment)


# ── PATCH /payments/{id}/confirm ──────────────────────────────────────────────

@router.patch("/payments/{payment_id}/confirm", response_model=PaymentResponse)
async def confirm_payment(
    payment_id: str,
    current_user: UserProfile = Depends(get_current_user),
):
    pm_result = (
        supabase.table("payments")
        .select("*")
        .eq("id", payment_id)
        .single()
        .execute()
    )

    if not pm_result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found.")

    payment = pm_result.data

    ag_result = (
        supabase.table("agreements")
        .select("*")
        .eq("id", payment["agreement_id"])
        .single()
        .execute()
    )

    if not ag_result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agreement not found.")

    agreement = ag_result.data

    if not _is_party_to_agreement(agreement, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a party to this agreement.",
        )

    if payment["payer_id"] == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot confirm your own payment.",
        )

    # Idempotent
    if payment["confirmed_by_receiver"]:
        return _build_payment_response(payment)

    now_iso = datetime.now(timezone.utc).isoformat()

    update_result = (
        supabase.table("payments")
        .update({
            "confirmed_by_receiver": True,
            "confirmed_at": now_iso,
        })
        .eq("id", payment_id)
        .execute()
    )

    if not update_result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm payment.",
        )

    confirmed_payment = update_result.data[0]

    # Notify payer — best effort
    try:
        payer = _get_profile_by_id(payment["payer_id"])
        if payer:
            receiver_name = current_user.full_name or current_user.email
            await email_service.send_payment_confirmed(
                to_email=payer["email"],
                to_name=payer.get("full_name") or payer["email"],
                receiver_name=receiver_name,
                amount=_format_amount(float(payment["amount"])),
                currency_symbol="₦",
                agreement_title=agreement["title"],
            )
    except Exception:
        pass

    # Check if agreement is now fully paid — best effort
    try:
        all_payments = (
            supabase.table("payments")
            .select("amount, confirmed_by_receiver")
            .eq("agreement_id", payment["agreement_id"])
            .execute()
        )
        total_paid = sum(
            float(p["amount"])
            for p in (all_payments.data or [])
            if p["confirmed_by_receiver"]
        )
        total_amount = float(agreement["amount"])

        if total_paid >= total_amount:
            # Mark agreement completed
            supabase.table("agreements").update({"status": "completed"}).eq(
                "id", payment["agreement_id"]
            ).execute()

            # Notify both parties
            initiator = _get_profile_by_id(agreement["initiator_id"])
            counterparty = (
                _get_profile_by_id(agreement["counterparty_id"])
                if agreement.get("counterparty_id")
                else None
            )
            amount_str = _format_amount(total_amount)

            for profile in [initiator, counterparty]:
                if profile:
                    try:
                        await email_service.send_agreement_completed(
                            to_email=profile["email"],
                            to_name=profile.get("full_name") or profile["email"],
                            agreement_title=agreement["title"],
                            total_amount=amount_str,
                            currency_symbol="₦",
                        )
                    except Exception:
                        pass
    except Exception:
        pass

    return _build_payment_response(confirmed_payment)
