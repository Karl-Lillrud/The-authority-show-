import requests

def submit_rss_to_spotify(access_token, rss_feed_url):
    """
    Submit the generated RSS feed URL to Spotify.
    """
    spotify_api_url = "https://api.spotify.com/v1/podcasts"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    data = {
        "rss_feed_url": rss_feed_url  # Submit the RSS feed URL, not raw XML
    }

    response = requests.post(spotify_api_url, headers=headers, json=data)

    if response.status_code == 201:
        print("Successfully uploaded RSS feed to Spotify")
        return True
    else:
        print(f"Error uploading RSS feed to Spotify: {response.status_code}")
        print(response.text)
        return False
