"""
frontend/app.py

Modern, sleek UI for LegalEase: collects document details, offers quick templates,
calls the FastAPI backend to generate legal documents via Gemini, and provides
an editable preview with TXT / DOCX / PDF downloads.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import requests

from config import LOGO_PATH, BACKEND_URL
from ai_core.generator import sanitize_text, format_docx, format_pdf, format_html_preview

st.set_page_config(
    page_title="LegalEase — AI Legal Document Studio",
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# --- Custom Styling ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .hero-container {
        text-align: center;
        padding: 24px 20px 18px 20px;
        background: linear-gradient(135deg, rgba(30, 58, 138, 0.25) 0%, rgba(15, 23, 42, 0.4) 100%);
        border: 1px solid rgba(59, 130, 246, 0.25);
        border-radius: 16px;
        backdrop-filter: blur(12px);
        margin-bottom: 24px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
    }

    .hero-badge {
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        color: #60A5FA;
        background: rgba(37, 99, 235, 0.15);
        border: 1px solid rgba(96, 165, 250, 0.3);
        padding: 4px 12px;
        border-radius: 9999px;
        margin-bottom: 10px;
    }

    .hero-title {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FFFFFF 40%, #93C5FD 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        line-height: 1.2;
    }

    .hero-subtitle {
        color: #94A3B8;
        font-size: 0.98rem;
        margin-top: 8px;
        margin-bottom: 0;
    }

    .glass-card {
        background: rgba(17, 24, 39, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 20px;
    }

    .preview-box {
        background: #0B0F19;
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 12px;
        padding: 20px;
        max-height: 480px;
        overflow-y: auto;
        box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.5);
    }

    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Hero Header ---
st.markdown(
    """
    <div class="hero-container">
        <span class="hero-badge">⚡ Powered by Gemini AI</span>
        <h1 class="hero-title">⚖️ LegalEase Studio</h1>
        <p class="hero-subtitle">Generate, customize, and export professional legal documents in seconds.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Document Template Presets ---
TEMPLATES = {
    "Custom (Blank)": {
        "doc_type": "",
        "parties": "",
        "terms": "",
    },
    "Freelance Contract": {
        "doc_type": "Freelance Work Contract",
        "parties": "Jane Doe (Service Provider), TechNova Inc. (Client)",
        "terms": "Payment within 30 days of invoice; Deliver work by agreed milestones; Confidentiality must be maintained; Either party may terminate with 15 days written notice; Intellectual property transfers upon full payment",
    },
    "Non-Disclosure Agreement (NDA)": {
        "doc_type": "Non-Disclosure Agreement",
        "parties": "Alpha Innovations LLC (Disclosing Party), Beta Solutions Ltd (Receiving Party)",
        "terms": "Recipient agrees not to disclose confidential information for a period of 2 years; Information used strictly for evaluation purposes; Return or destroy materials upon written request",
    },
    "Employment Agreement": {
        "doc_type": "Employment Agreement",
        "parties": "Acme Corp (Employer), Alex Smith (Employee)",
        "terms": "Full-time position as Senior Software Engineer; 40 hours per week; Compensation of $120,000 annually paid semi-monthly; 20 days paid time off; 30 days termination notice required",
    },
    "Residential Lease Agreement": {
        "doc_type": "Residential Lease Agreement",
        "parties": "Robert Johnson (Landlord), Sarah Miller (Tenant)",
        "terms": "12-month lease period; Monthly rent of $2,000 due on the 1st of each month; Security deposit of $2,000; No unauthorized subleasing; Tenant responsible for electric and water utilities",
    },
}

with st.expander("⚡ Quick Document Templates", expanded=False):
    selected_preset = st.selectbox(
        "Select a pre-filled template to get started quickly:",
        list(TEMPLATES.keys()),
        index=0,
    )

preset_data = TEMPLATES[selected_preset]

# --- Inputs Form ---
st.markdown("<h4 style='color:#93C5FD;margin-bottom:12px;'>📝 Document Specifications</h4>", unsafe_allow_html=True)

col_t1, col_t2 = st.columns([2, 1])
with col_t1:
    document_type = st.text_input(
        "Document Type",
        value=preset_data["doc_type"],
        placeholder="e.g. Freelance Agreement, NDA, Lease Contract",
    )
with col_t2:
    dates = st.text_input(
        "Effective Date",
        value="September 26, 2026",
        placeholder="e.g. October 1, 2026",
    )

parties = st.text_area(
    "Parties Involved",
    value=preset_data["parties"],
    placeholder="e.g. Jane Doe (Provider), TechNova Inc. (Client)",
    help="List all parties and their roles",
    height=85,
)

terms = st.text_area(
    "Terms & Clauses (separate items with semicolons ;)",
    value=preset_data["terms"],
    placeholder="e.g. Payment due within 30 days; Confidentiality clause; 15 days termination notice",
    help="Each clause will be drafted into a dedicated section",
    height=110,
)

if "generated_text" not in st.session_state:
    st.session_state.generated_text = ""
if "show_edit" not in st.session_state:
    st.session_state.show_edit = False

btn_col1, btn_col2 = st.columns([2, 1])
with btn_col1:
    generate_clicked = st.button("✨ Generate Legal Document", type="primary", use_container_width=True)
with btn_col2:
    if st.button("🔄 Clear All", use_container_width=True):
        st.session_state.generated_text = ""
        st.session_state.show_edit = False
        st.rerun()

if generate_clicked:
    if not (document_type and parties and terms and dates):
        st.warning("⚠️ Please fill in all fields before generating.")
    else:
        with st.spinner("🤖 Drafting your tailored legal document with Gemini AI..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/generate",
                    json={
                        "document_type": document_type,
                        "parties": parties,
                        "terms": terms,
                        "dates": dates,
                    },
                    timeout=60,
                )
                if response.status_code == 200:
                    st.session_state.generated_text = sanitize_text(
                        response.json()["document"]
                    )
                    st.success("✅ Legal draft generated successfully!")
                else:
                    detail = response.json().get("detail", response.text)
                    st.error(f"Generation error: {detail}")
            except requests.exceptions.ConnectionError:
                st.error(
                    "❌ Unable to connect to the backend server. Please verify FastAPI is running at `http://127.0.0.1:8000`."
                )

# --- Preview & Actions ---
if st.session_state.generated_text:
    st.markdown("---")
    head_col1, head_col2 = st.columns([3, 1])
    with head_col1:
        st.markdown("<h4 style='color:#60A5FA;margin:0;'>📄 Document Preview & Export</h4>", unsafe_allow_html=True)
    with head_col2:
        if st.button("✏️ " + ("Hide Editor" if st.session_state.show_edit else "Edit Draft")):
            st.session_state.show_edit = not st.session_state.show_edit
            st.rerun()

    if st.session_state.show_edit:
        st.markdown("<small style='color:#94A3B8;'>Edit clauses or wording directly below:</small>", unsafe_allow_html=True)
        edited_text = st.text_area(
            "Live Document Editor",
            st.session_state.generated_text,
            height=320,
            label_visibility="collapsed",
        )
        st.session_state.generated_text = edited_text

    # Styled Visual Preview Box
    styled_html = format_html_preview(st.session_state.generated_text)
    st.markdown(f"<div class='preview-box'>{styled_html}</div>", unsafe_allow_html=True)

    text = st.session_state.generated_text
    safe_name = document_type.strip().replace(" ", "_").lower() or "legal_document"

    st.markdown("<p style='margin-top:14px;margin-bottom:6px;font-weight:600;color:#CBD5E1;'>📥 Download Formats:</p>", unsafe_allow_html=True)
    d_col1, d_col2, d_col3 = st.columns(3)

    with d_col1:
        st.download_button(
            "📄 Plain Text (.TXT)",
            data=text,
            file_name=f"{safe_name}.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with d_col2:
        st.download_button(
            "📝 Word (.DOCX)",
            data=format_docx(text, document_type or "Legal Document"),
            file_name=f"{safe_name}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
    with d_col3:
        st.download_button(
            "🔴 PDF Document (.PDF)",
            data=format_pdf(text, document_type or "Legal Document"),
            file_name=f"{safe_name}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

