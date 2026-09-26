"""
legalEaseAPI/routes.py

Defines the DocumentRequest schema and the /generate endpoint that
bridges the Streamlit frontend to the Gemini-powered document generator.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ai_core.gemini_generator import GeminiDocumentGenerator

router = APIRouter()

_generator = None


def get_generator() -> GeminiDocumentGenerator:
    """Lazily initializes the Gemini generator so the app can still start
    (and serve non-AI routes) even if the API key isn't configured yet."""
    global _generator
    if _generator is None:
        _generator = GeminiDocumentGenerator()
    return _generator


class DocumentRequest(BaseModel):
    document_type: str
    parties: str
    terms: str
    dates: str


@router.post("/generate")
def generate_legal_document(request: DocumentRequest):
    try:
        generator = get_generator()
        response = generator.generate_document(
            request.document_type,
            request.parties,
            request.terms,
            request.dates,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gemini generation failed: {e}")

    return {"document": response}
