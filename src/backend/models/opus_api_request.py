import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the OPUS API key from environment variables
api_key = os.getenv("OPUS_API_KEY")

# Define API URL
url = "https://api.opus.com/v1/generate_short"

# Data to send to the API (adjust parameters as needed)
data = {
    "api_key": api_key,
    "content": "Generate a short video about the latest tech trends.",
    "format": "mp4",
    "length": 60  # Adjust the length of the short
}

# Send the request to the OPUS API
response = requests.post(url, json=data)

# Check if the request was successful
if response.status_code == 200:
    # Print the generated short URL or video ID
    print("Short generated successfully:", response.json())
else:
    print("Error generating short:", response.status_code, response.text)