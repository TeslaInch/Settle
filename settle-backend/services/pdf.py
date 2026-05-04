import io
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)

# ── Brand colours ─────────────────────────────────────────────────────────────
_GREEN = colors.HexColor("#1B4332")
_GRAY = colors.HexColor("#6B7280")
_LIGHT_GRAY = colors.HexColor("#F3F4F6")
_BORDER = colors.HexColor("#E5E7EB")
_BLACK = colors.HexColor("#111827")
_RED = colors.HexColor("#DC2626")


def _styles() -> dict:
    base = getSampleStyleSheet()

    def s(name, **kw) -> ParagraphStyle:
        return ParagraphStyle(name, parent=base["Normal"], **kw)

    return {
        "brand": s("brand", fontSize=26, textColor=_GREEN, fontName="Helvetica-Bold",
                   spaceAfter=1 * mm),
        "subheader": s("subheader", fontSize=10, textColor=_GRAY, spaceAfter=4 * mm),
        "title": s("title", fontSize=16, textColor=_BLACK, fontName="Helvetica-Bold",
                   spaceAfter=2 * mm),
        "status": s("status", fontSize=10, textColor=_GRAY, spaceAfter=4 * mm),
        "label": s("label", fontSize=8, textColor=_GRAY, fontName="Helvetica-Bold",
                   spaceAfter=1 * mm, leading=10),
        "body": s("body", fontSize=10, textColor=_BLACK, spaceAfter=2 * mm, leading=14),
        "body_small": s("body_small", fontSize=9, textColor=_BLACK, leading=13),
        "amount": s("amount", fontSize=22, textColor=_BLACK, fontName="Helvetica-Bold",
                    spaceAfter=1 * mm),
        "seal": s("seal", fontSize=9, textColor=_GRAY, leading=13, spaceAfter=1 * mm),
        "footer": s("footer", fontSize=8, textColor=_GRAY, alignment=TA_CENTER,
                    leading=12),
        "section_head": s("section_head", fontSize=10, textColor=_BLACK,
                          fontName="Helvetica-Bold", spaceAfter=2 * mm),
    }


def _hr(width: float = 160 * mm) -> HRFlowable:
    return HRFlowable(width=width, thickness=0.5, color=_BORDER, spaceAfter=4 * mm,
                      spaceBefore=4 * mm)


class PDFService:

    async def generate_agreement_pdf(
        self,
        agreement: dict,
        initiator: dict,
        counterparty: dict,
        payments: list,
    ) -> bytes:
        """
        Build a clean A4 PDF for the given agreement and return it as bytes.
        All arguments are plain dicts as returned by Supabase.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        st = _styles()
        page_width = A4[0] - 40 * mm  # usable width
        elements = []

        # ── 1. Header ─────────────────────────────────────────────────────────
        elements.append(Paragraph("SETTLE", st["brand"]))
        elements.append(Paragraph("Official Agreement Record", st["subheader"]))
        elements.append(_hr(page_width))

        # ── 2. Agreement title + status ───────────────────────────────────────
        elements.append(Paragraph(agreement.get("title", "Untitled Agreement"), st["title"]))
        status_raw = agreement.get("status", "pending")
        elements.append(Paragraph(f"Status: {status_raw.capitalize()}", st["status"]))

        # ── 3. Two-column parties ─────────────────────────────────────────────
        initiator_name = initiator.get("full_name") or "—"
        initiator_email = initiator.get("email") or "—"

        cp_name = counterparty.get("full_name") or "Pending"
        cp_email = counterparty.get("email") or agreement.get("counterparty_email") or "—"

        left_text = (
            f"<b>Initiated by:</b> {initiator_name}<br/>"
            f"<font color='#6B7280'>Email: {initiator_email}</font>"
        )
        right_text = (
            f"<b>Counterparty:</b> {cp_name}<br/>"
            f"<font color='#6B7280'>Email: {cp_email}</font>"
        )

        col_w = page_width / 2 - 3 * mm
        party_table = Table(
            [[Paragraph(left_text, st["body_small"]),
              Paragraph(right_text, st["body_small"])]],
            colWidths=[col_w, col_w],
        )
        party_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        elements.append(party_table)
        elements.append(_hr(page_width))

        # ── 4. Amount ─────────────────────────────────────────────────────────
        elements.append(Paragraph("Amount", st["label"]))
        amount_val = float(agreement.get("amount", 0))
        elements.append(Paragraph(f"&#8358;{amount_val:,.2f}", st["amount"]))

        repayment = str(agreement.get("repayment_date", ""))[:10]
        elements.append(Paragraph(f"Repayment Date: {repayment}", st["body"]))
        elements.append(_hr(page_width))

        # ── 5. Terms ──────────────────────────────────────────────────────────
        elements.append(Paragraph("Agreement Terms", st["label"]))
        terms_text = (agreement.get("terms") or "").replace("\n", "<br/>")
        elements.append(Paragraph(terms_text, st["body"]))

        # ── 6. Seal section ───────────────────────────────────────────────────
        sealed_at = agreement.get("sealed_at")
        seal_hash = agreement.get("seal_hash")
        if sealed_at:
            elements.append(_hr(page_width))
            # Format sealed_at nicely
            try:
                dt = datetime.fromisoformat(str(sealed_at).replace("Z", "+00:00"))
                sealed_str = dt.strftime("%d %b %Y, %H:%M UTC")
            except Exception:
                sealed_str = str(sealed_at)[:19]

            elements.append(Paragraph(f"Sealed on {sealed_str}", st["seal"]))
            if seal_hash:
                short_hash = str(seal_hash)[:32]
                elements.append(
                    Paragraph(f"Record fingerprint: {short_hash}...", st["seal"])
                )

        # ── 7. Payments section ───────────────────────────────────────────────
        if payments:
            elements.append(_hr(page_width))
            elements.append(Paragraph("Payment History", st["section_head"]))

            header_row = [
                Paragraph("<b>Date</b>", st["body_small"]),
                Paragraph("<b>Amount</b>", st["body_small"]),
                Paragraph("<b>Status</b>", st["body_small"]),
            ]
            data_rows = [header_row]

            total_paid = 0.0
            for p in payments:
                logged = str(p.get("logged_at", ""))[:10]
                amt = float(p.get("amount", 0))
                confirmed = p.get("confirmed_by_receiver", False)
                if confirmed:
                    total_paid += amt
                status_label = "Confirmed" if confirmed else "Pending"

                data_rows.append([
                    Paragraph(logged, st["body_small"]),
                    Paragraph(f"&#8358;{amt:,.2f}", st["body_small"]),
                    Paragraph(status_label, st["body_small"]),
                ])

            col_widths = [page_width * 0.35, page_width * 0.35, page_width * 0.30]
            pay_table = Table(data_rows, colWidths=col_widths)
            pay_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), _LIGHT_GRAY),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _LIGHT_GRAY]),
                ("GRID", (0, 0), (-1, -1), 0.4, _BORDER),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            elements.append(pay_table)
            elements.append(Spacer(1, 3 * mm))
            elements.append(
                Paragraph(f"Total Confirmed Paid: &#8358;{total_paid:,.2f}", st["body"])
            )

        # ── 8. Footer ─────────────────────────────────────────────────────────
        elements.append(Spacer(1, 8 * mm))
        elements.append(_hr(page_width))
        agreement_id = str(agreement.get("id", ""))
        short_id = agreement_id[:16] if agreement_id else "—"
        generated = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")

        elements.append(
            Paragraph(
                "This agreement was sealed by mutual consent.",
                st["footer"],
            )
        )
        elements.append(
            Paragraph("Generated by Settle — settle.app", st["footer"])
        )
        elements.append(
            Paragraph(f"Record ID: {short_id} &nbsp;|&nbsp; {generated}", st["footer"])
        )

        doc.build(elements)
        return buffer.getvalue()


pdf_service = PDFService()
