from flask import g, redirect, render_template, url_for, Blueprint
from backend.repository.podcast_repository import PodcastRepository
from backend.repository.episode_repository import EpisodeRepository
import logging

landingpage_bp = Blueprint("landingpage_bp", __name__)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR)

# ✅ Initialize the repository
podcast_repo = PodcastRepository()
episode_repo = EpisodeRepository()

@landingpage_bp.route('/episode', methods=['GET'])
def episode():
    try:
        if not hasattr(g, 'user_id'):
            g.user_id = "test_user"
        if not g.user_id:
            return redirect(url_for('signin_bp.signin'))
        return render_template('landingpage/landingpage.html')
    except Exception as e:
        return f"Error: {str(e)}", 500

def map_social_links(social_links):
    platform_keywords = {
        "instagram": "instagram.com",
        "twitter": "x",
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
        # ✅ Get the user ID from the session 
        user_id = getattr(g, 'user_id', "test_user")

        # ✅ Fetch podcast details 
        podcast_doc, status_code = podcast_repo.get_podcast_by_id(user_id, podcast_id)

        if status_code != 200:
            logger.warning(f"⚠️ Podcast {podcast_id} not found!")
            return render_template("404.html")

        # ✅ Fetch episodes using the repository
        episodes_response, status_code = episode_repo.get_episodes_by_podcast(podcast_id, user_id)

        if status_code != 200:
            logger.error(f"Failed to fetch episodes for podcast {podcast_id}: {episodes_response}")
            episodes_list = []
        else:
            episodes_list = episodes_response.get("episodes", [])

        # ✅ Convert social media links to dictionary
        social_media_links = map_social_links(podcast_doc.get("podcast", {}).get("socialMedia", []))

        # ✅ Extract podcast details
        podcast_title = podcast_doc.get("podcast", {}).get("podName", "Default Podcast Title")
        podcast_description = podcast_doc.get("podcast", {}).get("description", "Default Podcast Description")
        host_name = podcast_doc.get("podcast", {}).get("hostName", "Unknown Host")
        host_bio = podcast_doc.get("podcast", {}).get("hostBio", "No biography available.")
        tagline = podcast_doc.get("podcast", {}).get("tagline", "No tagline available.")
        banner_url = podcast_doc.get("podcast", {}).get("bannerUrl", "")
        podcast_logo = podcast_doc.get("podcast", {}).get("logoUrl", "")
        host_image = podcast_doc.get("podcast", {}).get("hostImage", "")

        # Ensure `podcast_logo` is a valid string before checking its type
        if isinstance(podcast_logo, str):
            if podcast_logo.startswith("data:image"):  
                # ✅ It's a base64 image, so we can use it directly
                pass  
            elif podcast_logo.startswith("http"):  
                # ✅ It's an external URL, check if it's accessible
                podcast_logo = podcast_logo  # Keep the existing URL
            else:  
                # ❌ If it's neither, set a default fallback image
                podcast_logo = url_for('static', filename='images/default.png')
        else:
            # ❌ If it's not a string at all, set a default image
            podcast_logo = url_for('static', filename='images/default.png')

        # Ensure host_image is a valid string before checking startswith()
        if not isinstance(host_image, str) or not host_image.startswith("data:image"):
            host_image = url_for('static', filename='images/default-host.png')

        # Ensure banner_url is a valid string before checking startswith()
        if not isinstance(banner_url, str) or not banner_url.startswith("data:image"):
            banner_url = url_for('static', filename='images/default-banner.png')

        # ✅ Render the template with optimized data retrieval
        return render_template(
            "landingpage/landingpage.html",
            podcast_title=podcast_title,
            podcast_description=podcast_description,
            host_name=host_name,
            podcast_logo=podcast_logo,
            host_bio=host_bio,
            host_image=host_image,
            tagline=tagline,
            social_media=social_media_links,
            episodes=episodes_list,
            banner_url=banner_url
        )

    except Exception as e:
        logger.error(f"Error loading landing page: {str(e)}")
        return f"Error: {str(e)}", 500