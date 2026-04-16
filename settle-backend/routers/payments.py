from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from core.database import supabase
from core.security import get_current_user
from models.schemas import PaymentLogRequest, PaymentResponse, UserProfile

router = APIRouter()


# ── helpers ───────────────────────────────────────────────────────────────────

def _is_party_to_agreement(agreement: dict, user_id: str) -> bool:
    """Check if user is either initiator or counterparty."""
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


# ── GET /agreements/{id}/payments ─────────────────────────────────────────────

@router.get("/agreements/{agreement_id}/payments", response_model=list[PaymentResponse])
async def list_payments(
    agreement_id: str,
    current_user: UserProfile = Depends(get_current_user),
):
    # 1. Fetch agreement
    ag_result = (
        supabase.table("agreements")
        .select("*")
        .eq("id", agreement_id)
        .single()
        .execute()
    )

    if not ag_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agreement not found.",
        )

    agreement = ag_result.data

    # 2. Verify user is a party
    if not _is_party_to_agreement(agreement, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a party to this agreement.",
        )

    # 3. Fetch payments
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
    # 1. Fetch agreement
    ag_result = (
        supabase.table("agreements")
        .select("*")
        .eq("id", agreement_id)
        .single()
        .execute()
    )

    if not ag_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agreement not found.",
        )

    agreement = ag_result.data

    # 2. Verify user is a party
    if not _is_party_to_agreement(agreement, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a party to this agreement.",
        )

    # 3. Check agreement is active
    if agreement["status"] != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot log payment on {agreement['status']} agreement.",
        )

    # 4. Calculate total paid so far
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

    # 5. Reject if payment exceeds remaining balance
    if body.amount > remaining:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment amount (₦{body.amount:,.2f}) exceeds remaining balance (₦{remaining:,.2f}).",
        )

    # 6. Insert payment
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

    return _build_payment_response(result.data[0])


# ── PATCH /payments/{id}/confirm ──────────────────────────────────────────────

@router.patch("/payments/{payment_id}/confirm", response_model=PaymentResponse)
async def confirm_payment(
    payment_id: str,
    current_user: UserProfile = Depends(get_current_user),
):
    # 1. Fetch payment
    pm_result = (
        supabase.table("payments")
        .select("*")
        .eq("id", payment_id)
        .single()
        .execute()
    )

    if not pm_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found.",
        )

    payment = pm_result.data

    # 2. Fetch agreement
    ag_result = (
        supabase.table("agreements")
        .select("*")
        .eq("id", payment["agreement_id"])
        .single()
        .execute()
    )

    if not ag_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agreement not found.",
        )

    agreement = ag_result.data

    # 3. Verify user is a party
    if not _is_party_to_agreement(agreement, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a party to this agreement.",
        )

    # 4. Verify user is the receiver (not the payer)
    if payment["payer_id"] == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot confirm your own payment.",
        )

    # 5. Check if already confirmed
    if payment["confirmed_by_receiver"]:
        # Idempotent — return success without error
        return _build_payment_response(payment)

    # 6. Confirm payment
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

    return _build_payment_response(update_result.data[0])
