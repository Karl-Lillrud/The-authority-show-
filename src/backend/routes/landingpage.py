from flask import g, redirect, render_template, url_for, Blueprint
from backend.repository.podcast_repository import PodcastRepository  # ✅ Import repository

from backend.database.mongo_connection import collection, podcasts, get_db, episodes  # Add import


landingpage_bp = Blueprint("landingpage_bp", __name__)

# ✅ Initialize the repository
podcast_repo = PodcastRepository()

@landingpage_bp.route('/episode', methods=['GET'])
def episode():
    try:
        if not hasattr(g, 'user_id'):
            g.user_id = "test_user"
        if not g.user_id:
            return redirect(url_for('signin_bp.signin'))
        return render_template('landingpage/episode.html')
    except Exception as e:
        return f"Error: {str(e)}", 500

def map_social_links(social_links):
    platform_keywords = {
        "instagram": "instagram.com",
        "twitter": "twitter.com",
        "facebook": "facebook.com",
        "linkedin": "linkedin.com",
        "youtube": "youtube.com",
        "tiktok": "tiktok.com",
    }

    social_media_dict = {}

    for link in social_links:
        matched_platform = "other"
        for platform, keyword in platform_keywords.items():
            if keyword in link:
                matched_platform = platform
                break  # Stop checking once we find a match
        
        social_media_dict[matched_platform] = link

    return social_media_dict

@landingpage_bp.route("/landingpage/<podcast_id>")
def landingpage_by_id(podcast_id):
    try:
        # Fetch podcast details from the Podcasts collection
        podcast_doc = podcasts.find_one({"_id": podcast_id})
        if not podcast_doc:
            return render_template("404.html")

        # Convert social media links to a dictionary
        social_media_links = map_social_links(podcast_doc.get("socialMedia", []))

        # Fetch episodes from the Episodes collection matching the podcast_id
        episodes_cursor = episodes.find({"podcast_id": podcast_id})
        mapped_episodes = []
        for ep in episodes_cursor:
            # Print to debug in console
            print("DEBUG Episode Document:", ep)

            # Access the top-level fields directly
            title = ep.get("title", "No Title")
            description = ep.get("description", "No Description")

            mapped_episodes.append({
                "_id": ep.get("_id"),
                "title": title,
                "description": description,
                # Add any other fields you want to pass along, e.g. "publishDate"
                "publishDate": ep.get("publishDate", "No date"),
                "duration": ep.get("duration", "Unknown Duration")
            })

        # Extract podcast details
        podcast_title = podcast_doc.get("podName", "Default Podcast Title")
        podcast_description = podcast_doc.get("description", "Default Podcast Description")
        host_name = podcast_doc.get("hostName", "Unknown Host")
        host_bio = podcast_doc.get("hostBio", "No biography available.")
        host_image = podcast_doc.get("hostImage", url_for('static', filename='images/default-host.png'))

        # Handle podcast logo (Base64 or default)
        podcast_logo = podcast_doc.get("logoUrl", "")
        if not podcast_logo.startswith("data:image"):
            podcast_logo = url_for('static', filename='images/default.png')

        # Render the landing page template with the updated episodes list
        return render_template(
            "landingpage/landingpage.html",
            podcast_title=podcast_title,
            podcast_description=podcast_description,
            host_name=host_name,
            podcast_logo=podcast_logo,
            host_bio=host_bio,
            host_image=host_image,
            social_media=social_media_links,
            episodes=mapped_episodes
        )

    except Exception as e:
        return f"Error: {str(e)}", 500