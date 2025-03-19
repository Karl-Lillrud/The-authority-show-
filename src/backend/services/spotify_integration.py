import requests
import os
from dotenv import load_dotenv

load_dotenv()

def upload_episode_to_spotify(access_token, podcast_title, podcast_description, podcast_audio_url):
    # Den här URL:en kanske måste uppdateras beroende på rätt API
    url = "https://api.spotify.com/v1/me/podcasts"  # Uppdatera med rätt URL för podcast publicering
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    metadata = {
        "title": podcast_title,
        "description": podcast_description,
        "audio_url": podcast_audio_url,  # URL till podcastens ljudfil
        "language": "sv",
        "category": "Technology",  # Justera kategori om nödvändigt
    }
    
    # Log metadata for debugging
    print(f"Metadata: {metadata}")

    response = requests.post(url, json=metadata, headers=headers)
    
    if response.status_code == 200:
        print("Podcast publicerad framgångsrikt på Spotify.")
        return response.json()  # Återvänd info om podcasten
    else:
        print(f"Fel vid publicering: {response.status_code} - {response.text}")
        return None
