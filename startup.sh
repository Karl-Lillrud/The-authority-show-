#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

# Check if the 'src' directory exists
if [ ! -d "/home/site/wwwroot/src" ]; then
  echo "❌ Error: '/home/site/wwwroot/src' directory not found. Ensure the application is deployed correctly."
  exit 1
fi

# Run streamlit
streamlit run /home/site/wwwroot/src/backend/routes/transcript/streamlit_transcription.py