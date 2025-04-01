#!/bin/bash

# Start Gunicorn (Flask) on port 8000
gunicorn --chdir /home/site/wwwroot/src --bind=0.0.0.0:8000 --timeout 600 app:app &

# Start Streamlit on port 8501
streamlit run /home/site/wwwroot/src/backend/routes/transcript/streamlit_transcription.py --server.port 8501 &

# Keep the script running
wait