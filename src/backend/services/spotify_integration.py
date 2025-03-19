import requests
import os
from dotenv import load_dotenv

load_dotenv()

def upload_episode_to_spotify(access_token, podcast_title, podcast_description, podcast_audio_url):
    # Correct Spotify API endpoint for uploading episodes
    url = "https://api.spotify.com/v1/episodes"  # Replace with the correct endpoint
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    metadata = {
        "title": podcast_title,
        "description": podcast_description,
        "audio_url": podcast_audio_url,  # Ensure this is a publicly accessible URL
        "language": "sv",
        "category": "Technology",  # Adjust category if necessary
    }
    
    # Log metadata for debugging
    print(f"Metadata: {metadata}")

    response = requests.post(url, json=metadata, headers=headers)
    
    if response.status_code == 201:
        print("Podcast published successfully on Spotify.")
        return response.json()  # Return info about the podcast
    else:
        print(f"Error publishing podcast: {response.status_code} - {response.text}")
        return None
