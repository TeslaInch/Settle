import logging

import resend

from core.config import settings

logger = logging.getLogger(__name__)

resend.api_key = settings.RESEND_API_KEY

# ── HTML helpers ──────────────────────────────────────────────────────────────

def _base_html(body_content: str) -> str:
    """Wrap content in a clean, centered email shell."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Settle</title>
</head>
<body style="margin:0;padding:0;background:#F9FAFB;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#F9FAFB;padding:32px 16px;">
    <tr>
      <td align="center">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #E5E7EB;">
          <!-- Header -->
          <tr>
            <td style="background:#1B4332;padding:24px 32px;">
              <span style="font-size:22px;font-weight:700;color:#ffffff;letter-spacing:-0.5px;">Settle</span>
            </td>
          </tr>
          <!-- Body -->
          <tr>
            <td style="padding:32px;">
              {body_content}
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="background:#F3F4F6;padding:16px 32px;border-top:1px solid #E5E7EB;">
              <p style="margin:0;font-size:12px;color:#9CA3AF;text-align:center;">
                Settle — Your agreements, witnessed and sealed.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _detail_box(rows: list[tuple[str, str]]) -> str:
    """Render a grey detail box with label/value rows."""
    items = "".join(
        f"""<tr>
          <td style="padding:6px 0;font-size:13px;color:#6B7280;width:140px;vertical-align:top;">{label}</td>
          <td style="padding:6px 0;font-size:13px;color:#111827;font-weight:600;">{value}</td>
        </tr>"""
        for label, value in rows
    )
    return f"""<table width="100%" cellpadding="0" cellspacing="0"
        style="background:#F9FAFB;border:1px solid #E5E7EB;border-radius:8px;padding:16px;margin:20px 0;">
      <tbody>{items}</tbody>
    </table>"""


def _button(label: str, url: str) -> str:
    return f"""<div style="text-align:center;margin:24px 0;">
      <a href="{url}"
         style="display:inline-block;background:#1B4332;color:#ffffff;font-size:15px;
                font-weight:600;text-decoration:none;padding:14px 32px;border-radius:10px;">
        {label}
      </a>
    </div>"""


def _p(text: str, style: str = "") -> str:
    return f'<p style="margin:0 0 12px;font-size:15px;color:#374151;line-height:1.6;{style}">{text}</p>'


# ── EmailService ──────────────────────────────────────────────────────────────

class EmailService:
    """
    Async email client using the Resend SDK.
    All public methods return bool — True on success, False on any failure.
    Failures are logged but never raised; the caller must never crash because
    a notification failed.
    """

    def _send(
        self,
        to: str,
        subject: str,
        html: str,
        attachments: list[dict] | None = None,
    ) -> bool:
        """
        Synchronous Resend send call wrapped in try/except.
        Returns True on success, False on any error.
        """
        params: dict = {
            "from": settings.FROM_EMAIL,
            "to": [to],
            "subject": subject,
            "html": html,
        }
        if attachments:
            params["attachments"] = attachments

        try:
            resend.Emails.send(params)
            return True
        except Exception as exc:
            logger.error("Email send failed | to=%s | subject=%s | error=%s", to, subject, exc)
            return False

    # ── Public methods ────────────────────────────────────────────────────────

    async def send_agreement_invite(
        self,
        to_email: str,
        to_name: str,
        initiator_name: str,
        agreement_title: str,
        amount: str,
        currency_symbol: str,
        terms: str,
        repayment_date: str,
        confirm_url: str,
    ) -> bool:
        body = "".join([
            _p(f"Hi {to_name},"),
            _p(f"{initiator_name} has sent you an agreement to review and confirm."),
            _detail_box([
                ("Agreement", agreement_title),
                ("Amount", f"{currency_symbol}{amount}"),
                ("Repayment date", repayment_date),
                ("Terms", terms),
            ]),
            _button("Review &amp; Confirm Agreement", confirm_url),
            _p("This link expires in 72 hours.", "font-size:13px;color:#9CA3AF;text-align:center;"),
        ])
        return self._send(
            to=to_email,
            subject=f"{initiator_name} wants to create an agreement with you on Settle",
            html=_base_html(body),
        )

    async def send_creation_confirmation(
        self,
        to_email: str,
        to_name: str,
        agreement_title: str,
        counterparty_email: str,
    ) -> bool:
        body = "".join([
            _p(f"Hi {to_name},"),
            _p(
                f"Your agreement <strong>'{agreement_title}'</strong> has been sent to "
                f"<strong>{counterparty_email}</strong> for confirmation."
            ),
            _p("You will be notified when they confirm."),
        ])
        return self._send(
            to=to_email,
            subject="Your agreement has been sent — Settle",
            html=_base_html(body),
        )

    async def send_sealed_confirmation(
        self,
        to_email: str,
        to_name: str,
        agreement_title: str,
        amount: str,
        currency_symbol: str,
        sealed_at: str,
        record_url: str,
        pdf_bytes: bytes,
    ) -> bool:
        body = "".join([
            _p(f"Hi {to_name},"),
            _p("Your agreement is now permanently sealed and protected."),
            _detail_box([
                ("Agreement", agreement_title),
                ("Amount", f"{currency_symbol}{amount}"),
                ("Sealed at", sealed_at),
            ]),
            _button("View Your Record", record_url),
            _p(
                "Your sealed agreement is attached as a PDF.",
                "font-size:13px;color:#6B7280;",
            ),
        ])

        safe_title = agreement_title[:20].replace("/", "-").replace("\\", "-")
        attachments = [
            {
                "filename": f"settle-{safe_title}.pdf",
                "content": list(pdf_bytes),
                "content_type": "application/pdf",
            }
        ]

        return self._send(
            to=to_email,
            subject=f"Agreement Sealed — {agreement_title}",
            html=_base_html(body),
            attachments=attachments,
        )

    async def send_payment_logged(
        self,
        to_email: str,
        to_name: str,
        payer_name: str,
        amount: str,
        currency_symbol: str,
        agreement_title: str,
        confirm_url: str,
    ) -> bool:
        body = "".join([
            _p(f"Hi {to_name},"),
            _p(
                f"<strong>{payer_name}</strong> has recorded a payment of "
                f"<strong>{currency_symbol}{amount}</strong> against "
                f"<strong>'{agreement_title}'</strong>."
            ),
            _p("Please confirm you received this payment."),
            _button("Confirm Receipt", confirm_url),
        ])
        return self._send(
            to=to_email,
            subject="Payment logged — please confirm receipt",
            html=_base_html(body),
        )

    async def send_payment_confirmed(
        self,
        to_email: str,
        to_name: str,
        receiver_name: str,
        amount: str,
        currency_symbol: str,
        agreement_title: str,
    ) -> bool:
        body = "".join([
            _p(f"Hi {to_name},"),
            _p(
                f"<strong>{receiver_name}</strong> confirmed receipt of "
                f"<strong>{currency_symbol}{amount}</strong> for "
                f"<strong>'{agreement_title}'</strong>."
            ),
        ])
        return self._send(
            to=to_email,
            subject="Payment confirmed ✓ — Settle",
            html=_base_html(body),
        )

    async def send_payment_reminder(
        self,
        to_email: str,
        to_name: str,
        agreement_title: str,
        amount: str,
        currency_symbol: str,
        due_date: str,
        agreement_url: str,
    ) -> bool:
        body = "".join([
            _p(f"Hi {to_name},"),
            _p(
                f"Your agreement <strong>'{agreement_title}'</strong> is due in 2 days."
            ),
            _detail_box([
                ("Amount due", f"{currency_symbol}{amount}"),
                ("Due date", due_date),
            ]),
            _button("View Agreement", agreement_url),
        ])
        return self._send(
            to=to_email,
            subject=f"Payment reminder — {agreement_title} due in 2 days",
            html=_base_html(body),
        )

    async def send_agreement_completed(
        self,
        to_email: str,
        to_name: str,
        agreement_title: str,
        total_amount: str,
        currency_symbol: str,
    ) -> bool:
        body = "".join([
            _p(f"Hi {to_name},"),
            _p(
                f"<strong>'{agreement_title}'</strong> has been fully settled."
            ),
            _detail_box([
                ("Total paid", f"{currency_symbol}{total_amount}"),
            ]),
            _p("Your permanent record is saved on Settle."),
        ])
        return self._send(
            to=to_email,
            subject=f"Agreement completed — {agreement_title}",
            html=_base_html(body),
        )


email_service = EmailService()
