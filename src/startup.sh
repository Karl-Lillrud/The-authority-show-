#!/bin/bash

# No need to change directory because the package is extracted to /home/site/wwwroot
# Start gunicorn on port 8000 using the app in app.py
gunicorn --bind 0.0.0.0:8000 app:app &

# Run streamlit on port 8501 (adjust the path if necessary)
streamlit run backend/routes/transcript/streamlit_transcription.py --server.port 8501 &

# Keep the script running
wait