"""
ai_core/gemini_generator.py

Wraps the Google Gemini 1.5 Pro model to generate structured legal documents
from user-provided document type, parties, terms, and effective date.
"""

import time
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted

from config import GEMINI_API_KEY, MODEL_NAME

FALLBACK_MODELS = [
    MODEL_NAME,
    "gemini-3.8-flash-lite",
    "gemini-3.7-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
]


class GeminiDocumentGenerator:
    def __init__(self):
        if not GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Add it to your .env file "
                "(see .env.example)."
            )
        genai.configure(api_key=GEMINI_API_KEY)

    def generate_document(self, document_type: str, parties: str, terms: str, dates: str) -> str:
        """
        Builds a structured prompt and calls Gemini to draft the legal document.
        Automatically retries and attempts fallback models if a 429 rate limit is hit.
        """
        prompt = (
            f"You are a legal drafting assistant. Generate a comprehensive, "
            f"professional legal document titled '{document_type}'.\n"
            f"Involved parties: {parties}\n"
            f"Effective Date: {dates}\n"
            f"Terms and conditions (each item should become its own clause): {terms}\n\n"
            "Requirements:\n"
            "- Use a clear formal legal structure with numbered sections "
            "(e.g. 1. Services, 2. Term and Termination, 3. Payment, "
            "4. Confidentiality, 5. Governing Law, etc. as relevant to the "
            "document type).\n"
            "- Start with a '## {document_type}' heading, then an opening "
            "paragraph naming the parties and the effective date.\n"
            "- Bold section headings using markdown '**Heading:**' style.\n"
            "- Where specific facts are missing (amounts, addresses, states), "
            "use clearly bracketed placeholders like [Dollar Amount] or "
            "[State] rather than inventing facts.\n"
            "- End with a signature block for each party.\n"
            "- Do not include any commentary outside of the document itself."
        )

        last_err = None
        # Try candidate models in sequence
        candidate_models = list(dict.fromkeys(FALLBACK_MODELS))
        for model_candidate in candidate_models:
            try:
                model = genai.GenerativeModel(model_candidate)
                response = model.generate_content(prompt)
                return response.text
            except ResourceExhausted as e:
                last_err = e
                # If quota limit hit for this specific model, try the next model candidate
                continue
            except Exception as e:
                last_err = e
                continue

        # If all candidates hit quota, raise with clear advice
        if isinstance(last_err, ResourceExhausted):
            raise RuntimeError("Gemini Free Tier quota limit reached (5 requests/min). Please wait 20-30 seconds and try again.")
        raise last_err or RuntimeError("Failed to generate document with available models.")
