import io
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

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
from services.email import email_service
from services.pdf import pdf_service
from services.notify import notify_service
from utils.agreement_lock import seal_agreement

router = APIRouter(prefix="/agreements", tags=["agreements"])


# ── helpers ───────────────────────────────────────────────────────────────────

def _format_amount(amount: float) -> str:
    return f"{amount:,.2f}"


def _build_agreement_response(row: dict, other_party_name: str | None = None) -> AgreementResponse:
    return AgreementResponse(
        id=row["id"],
        title=row["title"],
        amount=float(row["amount"]),
        terms=row["terms"],
        status=row["status"],
        initiator_id=row["initiator_id"],
        initiator_email=row.get("initiator_email"),
        initiator_name=row.get("initiator_name"),
        counterparty_id=row.get("counterparty_id"),
        counterparty_email=row["counterparty_email"],
        counterparty_name=row.get("counterparty_name"),
        other_party_name=other_party_name,
        repayment_date=row["repayment_date"],
        seal_hash=row.get("seal_hash"),
        seal_payload=row.get("seal_payload"),
        sealed_at=row.get("sealed_at"),
        created_at=row["created_at"],
    )


def _get_profile_by_id(user_id: str) -> dict | None:
    result = (
        supabase.table("profiles")
        .select("id, email, full_name")
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )
    return result.data if result else None


def _get_profile_by_email(email: str) -> dict | None:
    result = (
        supabase.table("profiles")
        .select("id, email, full_name")
        .eq("email", email)
        .maybe_single()
        .execute()
    )
    return result.data


def _enrich_agreement(row: dict) -> dict:
    """Attach initiator/counterparty names and emails from profiles."""
    initiator = _get_profile_by_id(row["initiator_id"])
    if initiator:
        row["initiator_email"] = initiator.get("email")
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
    confirm_url = f"{settings.FRONTEND_URL}/agreements/confirm/{token}"

    insert_data = {
        "title": body.title,
        "amount": body.amount,
        "terms": body.terms,
        "initiator_id": current_user.id,
        "counterparty_email": body.counterparty_email,
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
    row["initiator_email"] = current_user.email
    row["initiator_name"] = current_user.full_name

    initiator_name = current_user.full_name or current_user.email

    # Notify counterparty — best effort
    try:
        await email_service.send_agreement_invite(
            to_email=body.counterparty_email,
            to_name=body.counterparty_email,
            initiator_name=initiator_name,
            agreement_title=body.title,
            amount=_format_amount(body.amount),
            currency_symbol="₦",
            terms=body.terms,
            repayment_date=body.repayment_date.strftime("%d %b %Y"),
            confirm_url=confirm_url,
        )
    except Exception:
        pass

    # Confirm to initiator — best effort
    try:
        await email_service.send_creation_confirmation(
            to_email=current_user.email,
            to_name=initiator_name,
            agreement_title=body.title,
            counterparty_email=body.counterparty_email,
        )
    except Exception:
        pass

    # Create notification for initiator
    notify_service.create(
        user_id=current_user.id,
        agreement_id=row["id"],
        type="agreement_created",
        message=f"Your agreement '{body.title}' has been sent to {body.counterparty_email}"
    )

    return _build_agreement_response(row)


# ── GET /agreements ───────────────────────────────────────────────────────────

@router.get("", response_model=list[AgreementResponse])
async def list_agreements(
    current_user: UserProfile = Depends(get_current_user),
):
    as_initiator = (
        supabase.table("agreements")
        .select("*")
        .eq("initiator_id", current_user.id)
        .order("created_at", desc=True)
        .execute()
    )

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

    rows.sort(key=lambda r: r["created_at"], reverse=True)

    result = []
    for row in rows:
        is_initiator = row["initiator_id"] == current_user.id
        if is_initiator:
            other_party_name = row.get("counterparty_name") or row.get("counterparty_email")
        else:
            other_party_name = row.get("initiator_name") or row.get("initiator_email")
        result.append(_build_agreement_response(row, other_party_name=other_party_name))

    return result


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
        .maybe_single()
        .execute()
    )

    if not result or not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agreement not found.")

    row = result.data

    if row["initiator_id"] != current_user.id and row.get("counterparty_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a party to this agreement.",
        )

    row = _enrich_agreement(row)
    is_initiator = row["initiator_id"] == current_user.id
    other_party_name = (
        row.get("counterparty_name") or row.get("counterparty_email")
        if is_initiator
        else row.get("initiator_name") or row.get("initiator_email")
    )
    return _build_agreement_response(row, other_party_name=other_party_name)


# ── GET /agreements/{id}/pdf ──────────────────────────────────────────────────

@router.get("/{agreement_id}/pdf")
async def download_agreement_pdf(
    agreement_id: str,
    current_user: UserProfile = Depends(get_current_user),
):
    """Generate and stream a PDF of the agreement using ReportLab."""
    # Fetch agreement
    ag_result = (
        supabase.table("agreements")
        .select("*")
        .eq("id", agreement_id)
        .maybe_single()
        .execute()
    )
    if not ag_result or not ag_result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agreement not found.")

    agreement = ag_result.data

    # Verify user is a party
    if (
        agreement["initiator_id"] != current_user.id
        and agreement.get("counterparty_id") != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a party to this agreement.",
        )

    # Fetch initiator profile
    initiator_result = (
        supabase.table("profiles")
        .select("id, email, full_name")
        .eq("id", agreement["initiator_id"])
        .maybe_single()
        .execute()
    )
    initiator = initiator_result.data or {}

    # Fetch counterparty profile (may not exist yet)
    counterparty: dict = {}
    if agreement.get("counterparty_id"):
        cp_result = (
            supabase.table("profiles")
            .select("id, email, full_name")
            .eq("id", agreement["counterparty_id"])
            .maybe_single()
            .execute()
        )
        counterparty = cp_result.data or {}

    # Fetch payments
    pm_result = (
        supabase.table("payments")
        .select("*")
        .eq("agreement_id", agreement_id)
        .order("logged_at")
        .execute()
    )
    payments = pm_result.data or []

    # Generate PDF bytes
    try:
        pdf_bytes = await pdf_service.generate_agreement_pdf(
            agreement=agreement,
            initiator=initiator,
            counterparty=counterparty,
            payments=payments,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {str(e)}",
        )

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="settle-{agreement_id[:8]}.pdf"'
        },
    )


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
        .maybe_single()
        .execute()
    )

    if not result or not result.data:
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

    # 3. Verify current user is the counterparty (by email or id)
    if agreement.get("counterparty_id") != current_user.id:
        if agreement.get("counterparty_email") != current_user.email:
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

    # 5. Fetch initiator profile
    initiator = _get_profile_by_id(agreement["initiator_id"])
    if not initiator:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve initiator profile.",
        )

    # 6. Seal the agreement
    seal = seal_agreement(
        agreement=agreement,
        initiator_email=initiator["email"],
        counterparty_email=current_user.email,
    )

    now_iso = datetime.now(timezone.utc).isoformat()

    # 7. Atomically log confirmation + seal via Postgres function
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

    # 8. Fetch sealed row
    sealed_result = (
        supabase.table("agreements")
        .select("*")
        .eq("id", agreement_id)
        .maybe_single()
        .execute()
    )
    if not sealed_result or not sealed_result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agreement sealed but could not be retrieved.",
        )

    sealed_row = sealed_result.data
    sealed_row["initiator_email"] = initiator["email"]
    sealed_row["initiator_name"] = initiator.get("full_name")
    sealed_row["counterparty_name"] = current_user.full_name

    record_url = f"{settings.FRONTEND_URL}/agreements/{agreement_id}"
    amount_str = _format_amount(float(agreement["amount"]))
    sealed_at_str = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")

    # 9. Generate PDF for attachment
    pdf_bytes = b""
    try:
        pdf_bytes = await pdf_service.generate_agreement_pdf(
            agreement=agreement,
            initiator=initiator,
            counterparty={
                "id": current_user.id,
                "email": current_user.email,
                "full_name": current_user.full_name,
            },
            payments=[],
        )
    except Exception:
        pass  # PDF failure must not block sealing

    # 10. Email both parties — best effort
    initiator_name = initiator.get("full_name") or initiator["email"]
    counterparty_name = current_user.full_name or current_user.email

    try:
        await email_service.send_sealed_confirmation(
            to_email=initiator["email"],
            to_name=initiator_name,
            agreement_title=agreement["title"],
            amount=amount_str,
            currency_symbol="₦",
            sealed_at=sealed_at_str,
            record_url=record_url,
            pdf_bytes=pdf_bytes,
        )
    except Exception:
        pass

    try:
        await email_service.send_sealed_confirmation(
            to_email=current_user.email,
            to_name=counterparty_name,
            agreement_title=agreement["title"],
            amount=amount_str,
            currency_symbol="₦",
            sealed_at=sealed_at_str,
            record_url=record_url,
            pdf_bytes=pdf_bytes,
        )
    except Exception:
        pass

    # Create notifications for both parties
    title = agreement["title"]
    agreement_id = agreement["id"]
    initiator_id = agreement["initiator_id"]

    # Notify initiator
    notify_service.create(
        user_id=initiator_id,
        agreement_id=agreement_id,
        type="agreement_sealed",
        message=f"'{title}' has been confirmed and sealed by both parties"
    )

    # Notify counterparty
    notify_service.create(
        user_id=current_user.id,
        agreement_id=agreement_id,
        type="agreement_sealed",
        message=f"You confirmed '{title}'. The agreement is now sealed."
    )

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
    """Resend the confirmation invite. Only the initiator can call this."""
    result = (
        supabase.table("agreements")
        .select("*")
        .eq("id", agreement_id)
        .maybe_single()
        .execute()
    )

    if not result or not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agreement not found.")

    agreement = result.data

    if agreement["initiator_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the initiator can resend the invite.",
        )

    if agreement["status"] != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot resend invite for a {agreement['status']} agreement.",
        )

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

    confirm_url = f"{settings.FRONTEND_URL}/agreements/confirm/{new_token}"
    initiator_name = current_user.full_name or current_user.email

    try:
        await email_service.send_agreement_invite(
            to_email=agreement["counterparty_email"],
            to_name=agreement["counterparty_email"],
            initiator_name=initiator_name,
            agreement_title=agreement["title"],
            amount=_format_amount(float(agreement["amount"])),
            currency_symbol="₦",
            terms=agreement["terms"],
            repayment_date=str(agreement["repayment_date"]),
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
    """
    result = (
        supabase.table("agreements")
        .select("*")
        .eq("confirmation_token", token)
        .maybe_single()
        .execute()
    )

    if not result or not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This confirmation link is invalid or has expired.",
        )

    agreement = result.data

    if agreement["status"] != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Agreement is already {agreement['status']}.",
        )

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

    initiator = _get_profile_by_id(agreement["initiator_id"])

    return {
        "id": agreement["id"],
        "title": agreement["title"],
        "amount": float(agreement["amount"]),
        "terms": agreement["terms"],
        "repayment_date": agreement["repayment_date"],
        "initiator_name": initiator.get("full_name") if initiator else None,
        "initiator_email": initiator.get("email") if initiator else None,
    }
