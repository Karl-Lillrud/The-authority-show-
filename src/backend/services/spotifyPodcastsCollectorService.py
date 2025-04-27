import re
import os
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from bs4 import BeautifulSoup
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = "Podmanager"
Podcasts_Collection = "Podcasts"

client = MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]
podcasts_collection = db[Podcasts_Collection]

# 🔑 Spotify API Credentials
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

# 🎵 Authenticate using Spotify OAuth
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope="user-read-email"
))


# 🔍 Function to Fetch Podcasts (Bypassing API Limit)
def fetch_spotify_podcasts():
    search_queries = ["podcast", "news podcast", "music podcast", "tech podcast", "sports podcast", "health podcast"]
    podcasts = set()  # Use a set to store unique podcasts
    limit = 50  # Max items per request
    max_offset = 1000  # API limit

    for query in search_queries:
        offset = 0
        print(f"\nSearching for podcasts with query: '{query}'")

        while offset < max_offset:
            results = sp.search(q=query, type="show", limit=limit, offset=offset)

            if 'shows' not in results or 'items' not in results['shows']:
                break  # Stop if no results

            items = results['shows']['items']
            if not items:
                break  # Stop when no more podcasts are returned

            for item in items:
                podcast_entry = (
                    item['name'],
                    item['external_urls']['spotify'],  # Spotify link
                    item.get('publisher', '')  # Publisher info (might contain website)
                )
                podcasts.add(podcast_entry)  # Using set to prevent duplicates

            offset += limit
            print(f"Fetched {len(podcasts)} unique podcasts so far...")  # Debugging output

    # Convert set to list of dictionaries
    return [{"title": p[0], "link": p[1], "publisher": p[2]} for p in podcasts]


# 📧 Function to Extract Emails and Title from a Webpage
def extract_info_from_url(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract title
            title = soup.title.string.strip() if soup.title else "No title found"

            # Extract emails
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            emails = re.findall(email_pattern, soup.get_text())

            return {"title": title, "emails": list(set(emails))}  # Remove duplicates
        else:
            print(f"Failed to fetch {url}, status code: {response.status_code}")
            return {"title": "No title found", "emails": []}
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return {"title": "No title found", "emails": []}


# 🚀 Main Execution
if __name__ == "__main__":
    print("Fetching Spotify podcasts...")
    spotify_podcasts = fetch_spotify_podcasts()

    print(f"Total unique podcasts fetched: {len(spotify_podcasts)}")

    # Extract emails from every link
    emails_found = []
    for podcast in spotify_podcasts:
        print(f"\nExtracting from: {podcast['title']} - {podcast['link']}")

        # Scrape the podcast link
        info = extract_info_from_url(podcast['link'])

        if info["emails"]:
            emails_found.append({"Podcast": podcast['title'], "Website": podcast['link'], "Title": info["title"],
                                 "Emails": info["emails"]})

    # 📌 Print Extracted Emails
    print("\nExtracted Podcast Emails:")
    # Spara alla med email
    for entry in emails_found:
        # Try to find matching Spotify podcast
        matching_spotify = next((p for p in spotify_podcasts if p["title"] == entry["Podcast"]), None)
        artwork_url = ""

        if matching_spotify:
            # Fetch Spotify data again to get full show details
            show_result = sp.search(q=entry["Podcast"], type="show", limit=1)
            if show_result["shows"]["items"]:
                item = show_result["shows"]["items"][0]
                artwork_url = item["images"][0]["url"] if "images" in item and item["images"] else ""

        doc = {
            "title": entry["Podcast"],
            "website": entry["Website"],
            "page_title": entry["Title"],
            "emails": entry["Emails"],
            "rss_url": "",
            "artwork_url": artwork_url  # ✅ New line added
        }

        if not podcasts_collection.find_one({"website": doc["website"]}):
            podcasts_collection.insert_one(doc)
            print(f"✅ Saved: {doc['title']} with artwork")
        else:
            print(f"🔁 Already exists: {doc['title']}")
