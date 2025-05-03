import re
import os
import sys
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from bs4 import BeautifulSoup
from pymongo import MongoClient
from dotenv import load_dotenv
import xml.etree.ElementTree as ET  # Add XML import
from xml.dom import minidom  # For pretty printing XML

load_dotenv()

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = "Podmanager"

client = MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]

# 🔑 Spotify API Credentials
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

# 🎵 Authenticate using Spotify OAuth
try:
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope="user-read-email",
            open_browser=False  # Prevent browser opening if not needed/possible
        )
    )
    # Attempt a simple API call to verify authentication
    sp.current_user()
    print("✅ Successfully authenticated with Spotify.")
except Exception as e:  # Catch potential exceptions during auth
    print(f"❌ Spotify Authentication Failed: {e}")
    print("Please ensure you are logged in to Spotify and have valid credentials.")
    sys.exit(1)  # Exit the script if authentication fails


# 🔍 Function to Fetch Podcasts (Bypassing API Limit)
def fetch_spotify_podcasts():
    search_queries = [
        "podcast",
        "news podcast",
        "music podcast",
        "tech podcast",
        "sports podcast",
        "health podcast",
    ]
    podcasts = set()  # Use a set to store unique podcasts
    limit = 50  # Max items per request
    max_offset = 1000  # API limit

    for query in search_queries:
        offset = 0
        print(f"\nSearching for podcasts with query: '{query}'")

        while offset < max_offset:
            results = sp.search(q=query, type="show", limit=limit, offset=offset)

            if "shows" not in results or "items" not in results["shows"]:
                break  # Stop if no results

            items = results["shows"]["items"]
            if not items:
                break  # Stop when no more podcasts are returned

            for item in items:
                podcast_entry = (
                    item["name"],
                    item["external_urls"]["spotify"],  # Spotify link
                    item.get("publisher", ""),  # Publisher info (might contain website)
                )
                podcasts.add(podcast_entry)  # Using set to prevent duplicates

            offset += limit
            print(
                f"Fetched {len(podcasts)} unique podcasts so far..."
            )  # Debugging output

    # Convert set to list of dictionaries
    return [{"title": p[0], "link": p[1], "publisher": p[2]} for p in podcasts]


# 📧 Function to Extract Emails and Title from a Webpage
def extract_info_from_url(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract title
            title = soup.title.string.strip() if soup.title else "No title found"

            # Extract emails
            email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
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
        info = extract_info_from_url(podcast["link"])

        if info["emails"]:
            emails_found.append(
                {
                    "Podcast": podcast["title"],
                    "Website": podcast["link"],
                    "Title": info["title"],
                    "Emails": info["emails"],
                }
            )

    # 📌 Process Extracted Emails and Prepare for XML/DB
    print("\nProcessing extracted podcast data...")
    podcasts_for_xml = []  # List to store data for XML export
    # Spara alla med email
    for entry in emails_found:
        # Try to find matching Spotify podcast
        matching_spotify = next(
            (p for p in spotify_podcasts if p["title"] == entry["Podcast"]), None
        )
        artwork_url = ""

        if matching_spotify:
            # Fetch Spotify data again to get full show details
            try:  # Add try-except for robustness
                show_result = sp.search(q=entry["Podcast"], type="show", limit=1)
                if show_result and show_result.get("shows", {}).get("items"):
                    item = show_result["shows"]["items"][0]
                    artwork_url = (
                        item["images"][0]["url"]
                        if "images" in item and item["images"]
                        else ""
                    )
            except Exception as search_err:
                print(f"⚠️ Error searching Spotify for artwork for {entry['Podcast']}: {search_err}")

        doc = {
            "title": entry["Podcast"],
            "website": entry["Website"],
            "page_title": entry["Title"],
            "emails": entry["Emails"],
            "rss_url": "",  # Keep placeholder or implement RSS finding if needed
            "artwork_url": artwork_url,
        }

        podcasts_for_xml.append(doc)  # Add doc to list for XML export

        # Save to MongoDB (optional, based on existing logic)
        if not podcasts_collection.find_one({"website": doc["website"]}):
            try:
                podcasts_collection.insert_one(doc)
                print(f"✅ Saved to DB: {doc['title']} with artwork")
            except Exception as db_err:
                print(f"❌ Error saving {doc['title']} to DB: {db_err}")
        else:
            print(f"🔁 Already exists in DB: {doc['title']}")

    # Generate XML file
    if podcasts_for_xml:
        print("\nGenerating XML file...")
        root = ET.Element("podcasts")

        for podcast_data in podcasts_for_xml:
            podcast_elem = ET.SubElement(root, "podcast")
            ET.SubElement(podcast_elem, "title").text = podcast_data.get("title", "")
            ET.SubElement(podcast_elem, "website").text = podcast_data.get("website", "")
            ET.SubElement(podcast_elem, "page_title").text = podcast_data.get("page_title", "")

            emails_elem = ET.SubElement(podcast_elem, "emails")
            for email in podcast_data.get("emails", []):
                ET.SubElement(emails_elem, "email").text = email

            ET.SubElement(podcast_elem, "rss_url").text = podcast_data.get("rss_url", "")
            ET.SubElement(podcast_elem, "artwork_url").text = podcast_data.get("artwork_url", "")

        # Pretty print XML
        xml_str = ET.tostring(root, encoding='unicode')
        dom = minidom.parseString(xml_str)
        pretty_xml_str = dom.toprettyxml(indent="  ")

        output_filename = "scraped_podcasts.xml"
        try:
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(pretty_xml_str)
            print(f"\n✅ Podcast data successfully saved to {output_filename}")
        except IOError as e:
            print(f"\n❌ Error writing XML file: {e}")
    else:
        print("\nℹ️ No podcasts with emails found to save to XML.")
