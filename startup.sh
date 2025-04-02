#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

# Run streamlit
streamlit run src/backend/routes/transcript/streamlit_transcription.py