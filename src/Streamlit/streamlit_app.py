import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Disable TensorFlow oneDNN optimizations
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# Ensure an asyncio event loop is running
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

if __name__ == "__main__":
    port = os.getenv("STREAMLIT_PORT", "8501")  # Default to 8501 if STREAMLIT_PORT is not set
    os.system(f"streamlit run src/backend/routes/transcript/streamlit_transcription.py --server.headless true --server.port {port}")
