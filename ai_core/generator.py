"""
ai_core/generator.py

Core formatting utilities that turn raw AI-generated text into
polished, branded output: sanitized text, a Word (.docx) document,
a PDF, and a styled HTML preview for the Streamlit frontend.
"""

import io
import re

from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from fpdf import FPDF

from config import LOGO_PATH


def sanitize_text(text: str) -> str:
    """Removes special/typographic characters so downstream formatters
    (docx, fpdf) don't choke on smart quotes, em-dashes, non-latin1, etc."""
    if not text:
        return ""
    replacements = {
        "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-",
        "\u2026": "...",
        "\u00a0": " ",
        "\u2022": "-",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    # Ensure text is pure latin-1 printable compatible
    text = text.encode("latin-1", "replace").decode("latin-1")
    # Strip any stray control characters except standard whitespace
    text = re.sub(r"[^\x09\x0A\x0D\x20-\x7E\xA0-\xFF]", "", text)
    return text.strip()


def _split_terms(terms_text: str):
    """Splits a semicolon-separated terms string into a clean list."""
    return [t.strip() for t in terms_text.split(";") if t.strip()]


def _parse_sections(text: str):
    """
    Very lightweight markdown-ish parser: splits the generated text into
    (heading, body) blocks based on lines that look like headings
    ('## Title', '**Heading:**', or numbered 'N. Heading').
    Falls back to treating the whole text as one block.
    """
    lines = text.splitlines()
    blocks = []
    current_heading = None
    current_body = []

    heading_pattern = re.compile(r"^(#{1,3}\s+.+|\*\*.+\*\*:?|^\d+\.\s+[A-Z][^\n]{0,60})$")

    for line in lines:
        stripped = line.strip()
        if heading_pattern.match(stripped):
            if current_heading is not None or current_body:
                blocks.append((current_heading, "\n".join(current_body).strip()))
            current_heading = re.sub(r"^#{1,3}\s+|\*\*|:$", "", stripped).strip()
            current_body = []
        else:
            current_body.append(line)

    blocks.append((current_heading, "\n".join(current_body).strip()))
    return [b for b in blocks if b[0] or b[1]]


# ---------------------------------------------------------------------------
# DOCX
# ---------------------------------------------------------------------------

def format_docx(text: str, doc_type: str) -> bytes:
    """Builds a formatted Word document: logo header, Times New Roman body,
    section headings, an auto-generated terms table (if terms are present
    as a flat list), and a footer."""
    text = sanitize_text(text)
    document = Document()

    style = document.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(11)

    # Logo header
    try:
        header_p = document.add_paragraph()
        header_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = header_p.add_run()
        run.add_picture(LOGO_PATH, width=Inches(1.5))
    except Exception:
        pass  # Logo optional if missing

    title_p = document.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_p.add_run(doc_type)
    title_run.bold = True
    title_run.font.size = Pt(16)

    document.add_paragraph()  # spacer

    for heading, body in _parse_sections(text):
        if heading:
            h = document.add_paragraph()
            hr = h.add_run(heading)
            hr.bold = True
            hr.font.size = Pt(13)
        if body:
            for para in body.split("\n\n"):
                para = para.strip()
                if para:
                    document.add_paragraph(para)

    # Footer
    section = document.sections[0]
    footer = section.footer
    footer_p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    footer_p.text = "LegalEase Inc. | contact@legalease.com | All Rights Reserved."
    footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    buf = io.BytesIO()
    document.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

class _LegalPDF(FPDF):
    def __init__(self, doc_type: str):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.doc_type = doc_type
        self.set_margins(15, 15, 15)
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        try:
            self.image(LOGO_PATH, x=(self.w - 30) / 2, y=8, w=30)
            self.ln(22)
        except Exception:
            self.ln(5)
        self.set_font("Helvetica", "B", 14)
        usable_w = self.w - self.l_margin - self.r_margin
        self.cell(usable_w, 8, self.doc_type, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        usable_w = self.w - self.l_margin - self.r_margin
        self.cell(usable_w, 10, "LegalEase Inc. | contact@legalease.com | All Rights Reserved.", align="C")


def format_pdf(text: str, doc_type: str) -> bytes:
    """Builds a branded PDF with a centered logo header, bold section
    headings, bullet-style terms, and a footer on every page."""
    text = sanitize_text(text)
    pdf = _LegalPDF(doc_type)
    pdf.add_page()
    usable_w = pdf.w - pdf.l_margin - pdf.r_margin

    for heading, body in _parse_sections(text):
        if heading:
            pdf.set_font("Helvetica", "B", 12)
            pdf.multi_cell(w=usable_w, h=7, text=heading)
            pdf.ln(1)
        if body:
            pdf.set_font("Helvetica", "", 10)
            for line in body.split("\n"):
                line = line.strip()
                if not line:
                    continue
                if line.startswith(("-", "*", "•")):
                    clean_line = f"  - {line.lstrip('-*• ').strip()}"
                    pdf.multi_cell(w=usable_w, h=5.5, text=clean_line)
                else:
                    pdf.multi_cell(w=usable_w, h=5.5, text=line)
            pdf.ln(2)

    return bytes(pdf.output())


# ---------------------------------------------------------------------------
# HTML preview
# ---------------------------------------------------------------------------

def format_html_preview(text: str) -> str:
    """Converts generated text into styled HTML blocks for an inline,
    dark-themed scrollable preview in the Streamlit frontend."""
    text = sanitize_text(text)
    html_parts = []
    for heading, body in _parse_sections(text):
        if heading:
            html_parts.append(
                f"<div style='margin-top:14px;margin-bottom:6px;padding-bottom:4px;border-bottom:1px solid rgba(59,130,246,0.3);'>"
                f"<span style='color:#60A5FA;font-size:1.05rem;font-weight:700;letter-spacing:0.5px;text-transform:uppercase;'>{heading}</span>"
                f"</div>"
            )
        if body:
            for para in body.split("\n\n"):
                para = para.strip()
                if not para:
                    continue
                if para.startswith(("-", "*", "•")):
                    items = "".join(
                        f"<li style='margin-bottom:6px;color:#E5E7EB;line-height:1.6;'>{line.lstrip('-*• ').strip()}</li>"
                        for line in para.split("\n") if line.strip()
                    )
                    html_parts.append(f"<ul style='margin-top:4px;margin-bottom:10px;padding-left:22px;'>{items}</ul>")
                else:
                    html_parts.append(f"<p style='color:#D1D5DB;line-height:1.65;font-size:0.95rem;margin-bottom:10px;'>{para}</p>")
    return "\n".join(html_parts)
