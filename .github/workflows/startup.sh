!/bin/bash

# Change to the src directory
cd /home/site/wwwroot/src

# Start gunicorn on port 8000
gunicorn --chdir src --bind 0.0.0.0:8000 --timeout 600 app:app &

# Run streamlit on a different port (e.g., 8501)
streamlit run src/backend/routes/transcript/streamlit_transcription.py --server.port 8501 &

# Keep the script running
wait