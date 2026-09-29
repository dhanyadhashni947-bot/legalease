import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

# Path to the LegalEase logo used in DOCX/PDF branding and the Streamlit UI
LOGO_PATH = os.path.join(os.path.dirname(__file__), "Image", "Logo.png")
INVERSE_LOGO_PATH = os.path.join(os.path.dirname(__file__), "Image", "inverseLogo.png")

# Backend URL the Streamlit frontend talks to
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
