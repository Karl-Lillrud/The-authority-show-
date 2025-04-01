#!/bin/bash

# Start Gunicorn (Flask) på port 8000
gunicorn --bind=0.0.0.0:8000 --timeout 600 app:app &

# Start Streamlit på port 8501
streamlit run backend/routes/transcript/streamlit_transcription.py --server.port 8501 &

# Håll scriptet igång
wait