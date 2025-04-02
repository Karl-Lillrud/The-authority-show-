#!/bin/bash

# Start Flask in the background
python src/app.py &

# Start Streamlit
streamlit run src/backend/routes/transcript/streamlit_transcription.py --server.port 8501 --server.address 0.0.0.0
