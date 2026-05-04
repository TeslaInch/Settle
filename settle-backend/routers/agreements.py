import secrets
import tempfile
import os
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
        .single()
        .execute()
    )
    return result.data


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
    """Generate and stream a PDF of the sealed agreement."""
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

    initiator = _get_profile_by_id(row["initiator_id"])
    counterparty = (
        _get_profile_by_id(row["counterparty_id"]) if row.get("counterparty_id") else None
    )

    payments_result = (
        supabase.table("payments")
        .select("*")
        .eq("agreement_id", agreement_id)
        .order("logged_at", desc=False)
        .execute()
    )
    payments = payments_result.data or []

    total_paid = sum(
        float(p["amount"]) for p in payments if p.get("confirmed_by_receiver")
    )

    # Build HTML for PDF
    payment_rows = "".join(
        f"""<tr>
          <td style="padding:6px 8px;border-bottom:1px solid #E5E7EB;font-size:12px;">
            {p.get('logged_at', '')[:10]}
          </td>
          <td style="padding:6px 8px;border-bottom:1px solid #E5E7EB;font-size:12px;">
            ₦{float(p['amount']):,.2f}
          </td>
          <td style="padding:6px 8px;border-bottom:1px solid #E5E7EB;font-size:12px;">
            {'Confirmed' if p.get('confirmed_by_receiver') else 'Pending'}
          </td>
          <td style="padding:6px 8px;border-bottom:1px solid #E5E7EB;font-size:12px;">
            {p.get('note') or '—'}
          </td>
        </tr>"""
        for p in payments
    )

    payments_section = f"""
    <h3 style="font-size:13px;color:#374151;margin:24px 0 8px;">Payment History</h3>
    <table width="100%" style="border-collapse:collapse;border:1px solid #E5E7EB;border-radius:6px;">
      <thead>
        <tr style="background:#F3F4F6;">
          <th style="padding:6px 8px;text-align:left;font-size:11px;color:#6B7280;">Date</th>
          <th style="padding:6px 8px;text-align:left;font-size:11px;color:#6B7280;">Amount</th>
          <th style="padding:6px 8px;text-align:left;font-size:11px;color:#6B7280;">Status</th>
          <th style="padding:6px 8px;text-align:left;font-size:11px;color:#6B7280;">Note</th>
        </tr>
      </thead>
      <tbody>{payment_rows}</tbody>
    </table>
    <p style="font-size:12px;color:#374151;margin-top:8px;">
      Total confirmed: <strong>₦{total_paid:,.2f}</strong>
    </p>
    """ if payments else ""

    seal_section = ""
    if row.get("seal_hash"):
        seal_section = f"""
        <div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:6px;padding:12px;margin-top:20px;">
          <p style="margin:0 0 4px;font-size:11px;font-weight:600;color:#065F46;text-transform:uppercase;letter-spacing:0.05em;">
            Agreement Fingerprint
          </p>
          <p style="margin:0;font-size:11px;font-family:monospace;color:#111827;word-break:break-all;">
            {row['seal_hash']}
          </p>
          <p style="margin:4px 0 0;font-size:10px;color:#6B7280;">
            Sealed at: {str(row.get('sealed_at', ''))[:19]} UTC
          </p>
        </div>
        """

    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <style>
    body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; margin: 0; padding: 32px; color: #111827; }}
    h1 {{ font-size: 20px; color: #1B4332; margin: 0 0 4px; }}
    h2 {{ font-size: 14px; color: #374151; margin: 20px 0 8px; }}
    .label {{ font-size: 11px; color: #6B7280; text-transform: uppercase; letter-spacing: 0.05em; }}
    .value {{ font-size: 14px; color: #111827; margin: 2px 0 12px; }}
    .header {{ border-bottom: 2px solid #1B4332; padding-bottom: 12px; margin-bottom: 20px; }}
    .meta {{ font-size: 11px; color: #9CA3AF; }}
  </style>
</head>
<body>
  <div class="header">
    <h1>Settle — Agreement Record</h1>
    <p class="meta">Generated: {datetime.now(timezone.utc).strftime('%d %b %Y, %H:%M UTC')}</p>
  </div>

  <p class="label">Agreement Title</p>
  <p class="value"><strong>{row['title']}</strong></p>

  <p class="label">Amount</p>
  <p class="value">₦{float(row['amount']):,.2f}</p>

  <p class="label">Status</p>
  <p class="value">{row['status'].capitalize()}</p>

  <p class="label">Repayment Date</p>
  <p class="value">{str(row['repayment_date'])[:10]}</p>

  <p class="label">Terms</p>
  <p class="value" style="white-space:pre-wrap;">{row['terms']}</p>

  <h2>Parties</h2>
  <p class="label">Initiator</p>
  <p class="value">
    {initiator.get('full_name') or ''} &lt;{initiator.get('email', '')}&gt;
  </p>

  <p class="label">Counterparty</p>
  <p class="value">
    {counterparty.get('full_name') or '' if counterparty else ''} &lt;{counterparty.get('email', '') if counterparty else row.get('counterparty_email', '')}&gt;
  </p>

  {payments_section}
  {seal_section}
</body>
</html>"""

    pdf_path = await pdf_service.generate_agreement_pdf(
        html_content=html_content,
        filename=f"settle-{agreement_id[:8]}",
    )

    def iter_file():
        try:
            with open(pdf_path, "rb") as f:
                yield from f
        finally:
            try:
                os.remove(pdf_path)
            except OSError:
                pass

    return StreamingResponse(
        iter_file(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="settle-agreement-{agreement_id[:8]}.pdf"'
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
        .single()
        .execute()
    )
    if not sealed_result.data:
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
        pdf_path = await pdf_service.generate_agreement_pdf(
            html_content=f"<html><body><h1>{agreement['title']}</h1></body></html>",
            filename=f"settle-{agreement_id[:8]}",
        )
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        os.remove(pdf_path)
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
        .single()
        .execute()
    )

    if not result.data:
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
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agreement not found.")

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
