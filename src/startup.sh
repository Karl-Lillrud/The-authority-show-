#!/bin/bash
gunicorn --bind 0.0.0.0:80 app:app &  # Changed to port 80
streamlit run backend/routes/transcript/streamlit_transcription.py --server.port 8501 &
wait