#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

# Check available disk space
if [ "$(df / | tail -1 | awk '{print $4}')" -lt 1048576 ]; then
  echo "Error: Not enough disk space available."
  exit 1
fi

# Start gunicorn in the background
gunicorn --chdir src --bind=0.0.0.0 --timeout 600 app:app &

# Run streamlit
streamlit run src/backend/routes/transcript/streamlit_transcription.py