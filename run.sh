#!/bin/bash
# Launch both the FastAPI backend and Streamlit frontend.
echo "Starting FastAPI backend on :8000 ..."
uvicorn legalEaseAPI.main:app --reload &
BACKEND_PID=$!
sleep 2
echo "Starting Streamlit frontend on :8501 ..."
streamlit run frontend/app.py
kill $BACKEND_PID
