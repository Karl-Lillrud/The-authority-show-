from flask import g, redirect, render_template, url_for, Blueprint
from backend.repository.podcast_repository import PodcastRepository  # ✅ Import repository

from backend.database.mongo_connection import collection, podcasts, get_db, episodes  # Add import


landingpage_bp = Blueprint("landingpage_bp", __name__)

# ✅ Initialize the repository
podcast_repo = PodcastRepository()

@landingpage_bp.route('/landingpage', methods=['GET'])
def landingpage():

    if not g.user_id:
        return redirect(url_for('signin_bp.signin'))

    # ✅ Use the repository to fetch podcast details
    podcast_data, status_code = PodcastRepository.get_podcasts(g.user_id)

    # ✅ If the user has no podcasts, return default values
    if status_code != 200 or not podcast_data["podcast"]:
        podcast_doc = None
    else:
        podcast_doc = podcast_data["podcast"][0]  # Get the first podcast (if multiple exist)

    # ✅ Extract podcast details (with safe defaults)
    podcast_title = podcast_doc.get("podName", "Default Podcast Title") if podcast_doc else "Default Podcast Title"
    podcast_description = podcast_doc.get("description", "Default Podcast Description") if podcast_doc else "Default Podcast Description"
    host_name = podcast_doc.get("hostName", "Unknown Host") if podcast_doc else "Unknown Host"
    social_media_links = podcast_doc.get("socialMedia", []) if podcast_doc else []
    

    # ✅ Debugging print statements
    print("DEBUG: SOCIAL MEDIA LINKS FROM DATABASE:", social_media_links)

    # ✅ Handle Podcast Logo (Base64 or Default)
    podcast_logo = podcast_doc.get("logoUrl", "") if podcast_doc else ""
    if not podcast_logo.startswith("data:image"):  # Ensure it's Base64
        podcast_logo = url_for('static', filename='images/default.png')

    # ✅ Fetch episodes using the repository
    episodes_data, status_code = podcast_repo.get_podcast_by_id(g.user_id, podcast_doc["_id"]) if podcast_doc else ({}, 200)
    episodes = episodes_data.get("podcast", {}).get("episodes", []) if status_code == 200 else []

    return render_template(
        'landingpage/landingpage.html',
        podcast_title=podcast_title,
        podcast_description=podcast_description,
        podcast_logo=podcast_logo,
        host_name=host_name,
        social_media=social_media_links,  # ✅ Correctly pass social media
        episodes=episodes
    )

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
    platforms = ["instagram", "twitter", "facebook", "linkedin", "youtube", "tiktok"]
    social_media_dict = {}

    for i, link in enumerate(social_links):
        platform = platforms[i] if i < len(platforms) else f"other{i}"
        social_media_dict[platform] = link

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

        # Fetch episodes from the Episodes collection
        episodes_data = episodes.find({"podcast_id": podcast_id})  # Assuming the episode documents contain a 'podcast_id' field
        episodes_list = list(episodes_data)

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

        return render_template(
            "landingpage/landingpage.html",
            podcast_title=podcast_title,
            podcast_description=podcast_description,
            host_name=host_name,
            podcast_logo=podcast_logo,
            host_bio=host_bio,
            host_image=host_image,
            social_media=social_media_links,  # Now a dictionary
            episodes=episodes_list  # Pass episodes to the template
        )
    
    except Exception as e:
        return f"Error: {str(e)}", 500
