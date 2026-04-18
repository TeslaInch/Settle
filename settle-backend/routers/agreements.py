import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from core.config import settings
from core.database import supabase
from core.security import get_current_user
from models.schemas import (
    AgreementCreate,
    AgreementResponse,
    ConfirmRequest,
    ConfirmResponse,
    UserProfile,
)
from services.whatsapp import whatsapp_service
from utils.agreement_lock import seal_agreement

router = APIRouter(prefix="/agreements", tags=["agreements"])


# ── helpers ───────────────────────────────────────────────────────────────────

def _format_amount(amount: float) -> str:
    return f"{amount:,.2f}"


def _build_agreement_response(row: dict) -> AgreementResponse:
    return AgreementResponse(
        id=row["id"],
        title=row["title"],
        amount=float(row["amount"]),
        terms=row["terms"],
        status=row["status"],
        initiator_id=row["initiator_id"],
        initiator_phone=row.get("initiator_phone"),
        initiator_name=row.get("initiator_name"),
        counterparty_id=row.get("counterparty_id"),
        counterparty_phone=row["counterparty_phone"],
        counterparty_name=row.get("counterparty_name"),
        repayment_date=row["repayment_date"],
        seal_hash=row.get("seal_hash"),
        seal_payload=row.get("seal_payload"),
        sealed_at=row.get("sealed_at"),
        created_at=row["created_at"],
    )


def _get_profile_by_id(user_id: str) -> dict | None:
    result = (
        supabase.table("profiles")
        .select("id, phone_number, full_name")
        .eq("id", user_id)
        .single()
        .execute()
    )
    return result.data


def _enrich_agreement(row: dict) -> dict:
    """Attach initiator/counterparty names and phones from profiles."""
    initiator = _get_profile_by_id(row["initiator_id"])
    if initiator:
        row["initiator_phone"] = initiator.get("phone_number")
        row["initiator_name"] = initiator.get("full_name")

    if row.get("counterparty_id"):
        cp = _get_profile_by_id(row["counterparty_id"])
        if cp:
            row["counterparty_name"] = cp.get("full_name")

    return row


# ── POST /agreements ──────────────────────────────────────────────────────────

@router.post("", response_model=AgreementResponse, status_code=status.HTTP_201_CREATED)
async def create_agreement(
    body: AgreementCreate,
    current_user: UserProfile = Depends(get_current_user),
):
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=72)

    confirm_url = (
        f"{settings.PRODUCTION_FRONTEND_URL}/agreements/confirm/{token}"
    )

    insert_data = {
        "title": body.title,
        "amount": body.amount,
        "terms": body.terms,
        "initiator_id": current_user.id,
        "counterparty_phone": body.counterparty_phone,
        "repayment_date": body.repayment_date.isoformat(),
        "status": "pending",
        "confirmation_token": token,
        "token_expires_at": expires_at.isoformat(),
    }

    result = supabase.table("agreements").insert(insert_data).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create agreement.",
        )

    row = result.data[0]
    row["initiator_phone"] = current_user.phone_number
    row["initiator_name"] = current_user.full_name

    # Notify counterparty — best effort, don't fail the request
    try:
        await whatsapp_service.send_agreement_invite(
            counterparty_phone=body.counterparty_phone,
            initiator_name=current_user.full_name or current_user.phone_number,
            agreement_title=body.title,
            amount=_format_amount(body.amount),
            currency_symbol="₦",
            repayment_date=body.repayment_date.strftime("%d %b %Y"),
            confirm_url=confirm_url,
        )
    except Exception:
        pass  # notification failure must not block agreement creation

    return _build_agreement_response(row)


# ── GET /agreements ───────────────────────────────────────────────────────────

@router.get("", response_model=list[AgreementResponse])
async def list_agreements(
    current_user: UserProfile = Depends(get_current_user),
):
    # Agreements where user is initiator
    as_initiator = (
        supabase.table("agreements")
        .select("*")
        .eq("initiator_id", current_user.id)
        .order("created_at", desc=True)
        .execute()
    )

    # Agreements where user is counterparty
    as_counterparty = (
        supabase.table("agreements")
        .select("*")
        .eq("counterparty_id", current_user.id)
        .order("created_at", desc=True)
        .execute()
    )

    seen: set[str] = set()
    rows: list[dict] = []

    for row in (as_initiator.data or []) + (as_counterparty.data or []):
        if row["id"] not in seen:
            seen.add(row["id"])
            rows.append(_enrich_agreement(row))

    # Re-sort merged list
    rows.sort(key=lambda r: r["created_at"], reverse=True)

    return [_build_agreement_response(r) for r in rows]


# ── GET /agreements/{id} ──────────────────────────────────────────────────────

@router.get("/{agreement_id}", response_model=AgreementResponse)
async def get_agreement(
    agreement_id: str,
    current_user: UserProfile = Depends(get_current_user),
):
    result = (
        supabase.table("agreements")
        .select("*")
        .eq("id", agreement_id)
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agreement not found.")

    row = result.data

    if row["initiator_id"] != current_user.id and row.get("counterparty_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a party to this agreement.",
        )

    return _build_agreement_response(_enrich_agreement(row))


# ── POST /agreements/{id}/confirm ─────────────────────────────────────────────

@router.post("/{agreement_id}/confirm", response_model=ConfirmResponse)
async def confirm_agreement(
    agreement_id: str,
    body: ConfirmRequest,
    current_user: UserProfile = Depends(get_current_user),
):
    # 1. Fetch agreement
    result = (
        supabase.table("agreements")
        .select("*")
        .eq("id", agreement_id)
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agreement not found.")

    agreement = result.data

    # 2. Validate token
    if agreement.get("confirmation_token") != body.confirmation_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid confirmation token.")

    expires_at_raw = agreement.get("token_expires_at")
    if expires_at_raw:
        expires_at = datetime.fromisoformat(expires_at_raw.replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > expires_at:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Confirmation link has expired.")

    # 3. Verify current user is the counterparty
    if agreement.get("counterparty_id") != current_user.id:
        # Counterparty may not have an account yet — match by phone
        if agreement.get("counterparty_phone") != current_user.phone_number:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the counterparty can confirm this agreement.",
            )

    # 4. Check agreement is still pending
    if agreement["status"] != "pending":
        if agreement["status"] == "active":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This agreement has already been confirmed.",
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Agreement is already {agreement['status']}.",
        )

    # 5. Fetch initiator profile for seal
    initiator = _get_profile_by_id(agreement["initiator_id"])
    if not initiator:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve initiator profile.",
        )

    # 6. Seal the agreement
    seal = seal_agreement(
        agreement=agreement,
        initiator_phone=initiator["phone_number"],
        counterparty_phone=current_user.phone_number,
    )

    now_iso = datetime.now(timezone.utc).isoformat()

    # 7. Atomically log confirmation + seal agreement via a Postgres function.
    #    Both writes happen inside a single DB transaction — if either fails,
    #    Postgres rolls back automatically. No manual cleanup needed.
    try:
        supabase.rpc(
            "seal_agreement_confirm",
            {
                "p_agreement_id": agreement_id,
                "p_user_id":      current_user.id,
                "p_seal_hash":    seal["seal_hash"],
                "p_seal_payload": seal["seal_payload"],
                "p_sealed_at":    now_iso,
            },
        ).execute()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to seal agreement: {str(exc)}",
        )

    # Fetch the freshly sealed row to build the response
    sealed_result = (
        supabase.table("agreements")
        .select("*")
        .eq("id", agreement_id)
        .single()
        .execute()
    )
    if not sealed_result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agreement sealed but could not be retrieved.",
        )

    sealed_row = sealed_result.data
    sealed_row["initiator_phone"] = initiator["phone_number"]
    sealed_row["initiator_name"] = initiator.get("full_name")
    sealed_row["counterparty_name"] = current_user.full_name

    record_url = f"{settings.PRODUCTION_FRONTEND_URL}/agreements/{agreement_id}"
    amount_str = _format_amount(float(agreement["amount"]))

    # 8. Notify both parties — best effort
    sealed_at_str = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")
    try:
        await whatsapp_service.send_sealed_confirmation(
            phone=initiator["phone_number"],
            party_name=initiator.get("full_name") or initiator["phone_number"],
            agreement_title=agreement["title"],
            amount=amount_str,
            currency_symbol="₦",
            sealed_at=sealed_at_str,
            record_url=record_url,
        )
    except Exception:
        pass

    try:
        await whatsapp_service.send_sealed_confirmation(
            phone=current_user.phone_number,
            party_name=current_user.full_name or current_user.phone_number,
            agreement_title=agreement["title"],
            amount=amount_str,
            currency_symbol="₦",
            sealed_at=sealed_at_str,
            record_url=record_url,
        )
    except Exception:
        pass

    return ConfirmResponse(
        message="Agreement sealed successfully.",
        agreement=_build_agreement_response(sealed_row),
    )


# ── POST /agreements/{id}/resend-invite ───────────────────────────────────────

@router.post("/{agreement_id}/resend-invite", status_code=status.HTTP_200_OK)
async def resend_invite(
    agreement_id: str,
    current_user: UserProfile = Depends(get_current_user),
):
    """
    Resend the confirmation invite to the counterparty.
    Only the initiator can call this.
    Issues a fresh token with a new 72-hour expiry.
    """
    result = (
        supabase.table("agreements")
        .select("*")
        .eq("id", agreement_id)
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agreement not found.")

    agreement = result.data

    # Only the initiator can resend
    if agreement["initiator_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the initiator can resend the invite.",
        )

    # Only makes sense for pending agreements
    if agreement["status"] != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot resend invite for a {agreement['status']} agreement.",
        )

    # Issue a fresh token
    new_token = secrets.token_urlsafe(32)
    new_expires_at = datetime.now(timezone.utc) + timedelta(hours=72)

    update_result = (
        supabase.table("agreements")
        .update({
            "confirmation_token": new_token,
            "token_expires_at": new_expires_at.isoformat(),
        })
        .eq("id", agreement_id)
        .execute()
    )

    if not update_result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh confirmation token.",
        )

    confirm_url = f"{settings.PRODUCTION_FRONTEND_URL}/agreements/confirm/{new_token}"

    # Notify counterparty — best effort
    try:
        await whatsapp_service.send_agreement_invite(
            counterparty_phone=agreement["counterparty_phone"],
            initiator_name=current_user.full_name or current_user.phone_number,
            agreement_title=agreement["title"],
            amount=_format_amount(float(agreement["amount"])),
            currency_symbol="₦",
            repayment_date=agreement["repayment_date"],
            confirm_url=confirm_url,
        )
    except Exception:
        pass

    return {"message": "Invite resent successfully.", "expires_in_hours": 72}


# ── GET /agreements/by-token/{token} (public) ─────────────────────────────────

@router.get("/by-token/{token}")
async def get_agreement_by_token(token: str):
    """
    Public endpoint — no auth required.
    Returns a preview of the agreement for the confirmation page.
    Returns 410 Gone if the token has expired.
    Returns 409 Conflict if already confirmed.
    """
    result = (
        supabase.table("agreements")
        .select("*")
        .eq("confirmation_token", token)
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agreement not found.")

    agreement = result.data

    # Already confirmed
    if agreement["status"] != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Agreement is already {agreement['status']}.",
        )

    # Token expired
    expires_at_raw = agreement.get("token_expires_at")
    if expires_at_raw:
        expires_at = datetime.fromisoformat(expires_at_raw.replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > expires_at:
            initiator = _get_profile_by_id(agreement["initiator_id"])
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Confirmation link has expired.",
                headers={"X-Initiator-Name": initiator.get("full_name", "") if initiator else ""},
            )

    # Return preview (no sensitive seal data)
    initiator = _get_profile_by_id(agreement["initiator_id"])

    return {
        "id": agreement["id"],
        "title": agreement["title"],
        "amount": float(agreement["amount"]),
        "terms": agreement["terms"],
        "repayment_date": agreement["repayment_date"],
        "initiator_name": initiator.get("full_name") if initiator else None,
        "initiator_phone": initiator.get("phone_number") if initiator else None,
    }
