#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

# Clean up unnecessary files to free up space
rm -rf /tmp/* /home/site/wwwroot/output.tar.gz

# Start gunicorn in the background
gunicorn --chdir src --bind=0.0.0.0 --timeout 600 app:app &

# Run streamlit
streamlit run src/backend/routes/transcript/streamlit_transcription.py