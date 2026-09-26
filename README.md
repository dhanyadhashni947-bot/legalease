# LegalEase — AI-Powered Legal Document Generator

## Setup
1. Create a virtual environment:
   python -m venv venv
   source venv/bin/activate   (or venv\Scripts\activate on Windows)

2. Install dependencies:
   pip install -r requirements.txt

3. Copy .env.example to .env and add your Gemini API key:
   cp .env.example .env
   # then edit .env and set GEMINI_API_KEY=your_key
   Get a key at: https://ai.google.dev/

4. (Optional) Add your logo images to Image/Logo.png and Image/inverseLogo.png.
   The app runs fine without them (falls back to a text header).

## Run
Terminal 1 — backend:
   uvicorn legalEaseAPI.main:app --reload

Terminal 2 — frontend:
   streamlit run frontend/app.py

Or use the helper script:
   ./run.sh

Then open http://localhost:8501
