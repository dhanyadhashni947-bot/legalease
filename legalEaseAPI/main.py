"""
legalEaseAPI/main.py

Initializes the FastAPI app, wires up the /generate router, and
exposes a root health-check endpoint.

Run with:
    uvicorn legalEaseAPI.main:app --reload
"""

import sys
import os

# Ensure project root is on the path so `config` and `ai_core` resolve
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from legalEaseAPI.routes import router

app = FastAPI(title="LegalEase - AI Legal Document Generator")

app.include_router(router)


@app.get("/")
def home():
    return {"message": "Welcome to LegalEase AI Legal Document Generator API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
