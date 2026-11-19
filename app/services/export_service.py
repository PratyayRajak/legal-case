"""Service for exporting structured Case Briefs to downloadable formats (PDF, DOCX, JSON)."""
from __future__ import annotations

import json
from datetime import datetime

from app.schemas.canonical import RevenueCaseBrief


class BriefExportService:
    """Exports case brief records into judge-ready documents with official legal disclaimer."""

    DISCLAIMER_TEXT = "AI-assisted summary. Verify against the source document."
    DISCLAIMER_HI = "एआई-सहायता प्राप्त सारांश। मूल दस्तावेज़ से सत्यापन करें।"

    @staticmethod
    def export_as_json(brief: RevenueCaseBrief) -> str:
        """Export as structured UTF-8 JSON."""
        data = brief.model_dump()
        data["exported_at"] = datetime.utcnow().isoformat()
        data["disclaimer"] = BriefExportService.DISCLAIMER_TEXT
        data["disclaimer_hi"] = BriefExportService.DISCLAIMER_HI
        return json.dumps(data, ensure_ascii=False, indent=2)

    @staticmethod
    def export_as_text_summary(brief: RevenueCaseBrief, lang: str = "en") -> str:
        """Export as formatted court-ready text brief."""
        lines = []
        lines.append("=" * 70)
        lines.append("        COURT BRIEF ENGINE — JUDICIAL CASE SUMMARY")
        lines.append("=" * 70)
        lines.append(f"LEGAL DISCLAIMER: {BriefExportService.DISCLAIMER_TEXT}")
        lines.append(f"कानूनी अस्वीकरण: {BriefExportService.DISCLAIMER_HI}")
        lines.append("-" * 70)

        # Case Header
        case_no = brief.case_number.value.original_string if brief.case_number.found and brief.case_number.value else "N/A"
        court = brief.court_name.value if brief.court_name.found else "N/A"
        level = brief.court_level.value.value if brief.court_level.found and brief.court_level.value else "N/A"
        ctype = brief.case_type.value if brief.case_type.found else "N/A"

        lines.append(f"CASE NUMBER       : {case_no}")
        lines.append(f"COURT NAME        : {court} ({level.upper()})")
        lines.append(f"CASE TYPE         : {ctype.upper()}")

        # Dates
        fdate = brief.filing_date.value.original_string if brief.filing_date.found and brief.filing_date.value else "N/A"
        hdate = brief.next_hearing_date.value.original_string if brief.next_hearing_date.found and brief.next_hearing_date.value else "N/A"
        status = brief.current_status.value.value if brief.current_status.found and brief.current_status.value else "N/A"

        lines.append(f"FILING DATE       : {fdate}")
        lines.append(f"NEXT HEARING DATE : {hdate}")
        lines.append(f"CURRENT STATUS    : {status.upper()}")
        lines.append("-" * 70)

        # Parties
        lines.append("PARTIES:")
        if brief.petitioners.found and brief.petitioners.value:
            pets = ", ".join(p.original for p in brief.petitioners.value)
            lines.append(f"  Petitioner(s)   : {pets}")
        else:
            lines.append("  Petitioner(s)   : Not specified / Not found")

        if brief.respondents.found and brief.respondents.value:
            resps = ", ".join(r.original for r in brief.respondents.value)
            lines.append(f"  Respondent(s)   : {resps}")
        else:
            lines.append("  Respondent(s)   : Not specified / Not found")

        lines.append("-" * 70)
        lines.append("PROVENANCE & CITATIONS:")
        for field_name in ["case_number", "filing_date", "current_status"]:
            f = getattr(brief, field_name, None)
            if f and f.citations:
                c = f.citations[0]
                lines.append(f"  [{field_name.upper()}]: Page {c.page} — \"{c.snippet}\"")

        lines.append("=" * 70)
        lines.append(f"Generated at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')} by Court Brief Engine")
        return "\n".join(lines)

    @staticmethod
    def export_as_pdf_bytes(brief: RevenueCaseBrief) -> bytes:
        """Generate lightweight court-ready PDF using PyMuPDF."""
        import fitz

        doc = fitz.open()
        page = doc.new_page(width=595, height=842)  # Standard A4 size
        text = BriefExportService.export_as_text_summary(brief)

        # Insert title & text into PDF
        rect = fitz.Rect(40, 40, 555, 800)
        page.insert_textbox(rect, text, fontsize=9.5, fontname="courier")

        pdf_bytes = bytes(doc.tobytes())
        doc.close()
        return pdf_bytes
