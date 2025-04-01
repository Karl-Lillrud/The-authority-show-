#!/bin/bash

# Define a persistent directory for cached dependencies
CACHE_DIR=/home/site/wwwroot/.cache/pip

# Ensure the cache directory exists
mkdir -p $CACHE_DIR

# Export pip cache directory
export PIP_CACHE_DIR=$CACHE_DIR

# Clear old log files
echo "Clearing old log files..."
rm -rf /home/LogFiles/*

# Clear pip cache if needed
echo "Clearing pip cache to free up space..."
rm -rf /home/site/wwwroot/.cache/pip

# Remove large unnecessary files in /wwwroot/
echo "Removing unnecessary files in /wwwroot/..."
find /home/site/wwwroot/ -type f -name "*.tar.gz" -exec rm -f {} \;

# Install dependencies if not already cached
if [ ! -d "$CACHE_DIR" ] || [ -z "$(ls -A $CACHE_DIR)" ]; then
  echo "Installing dependencies..."
  python -m pip install --upgrade pip
  pip install -r /home/site/wwwroot/requirements.txt
else
  echo "Using cached dependencies..."
fi

# Start gunicorn in the background
gunicorn --chdir src --bind=0.0.0.0 --timeout 600 app:app &

# Run streamlit
streamlit run src/backend/routes/transcript/streamlit_transcription.py
