from flask import g, redirect, render_template, url_for, Blueprint
from backend.repository.podcast_repository import PodcastRepository
from backend.repository.episode_repository import EpisodeRepository
import logging
import base64
import requests
from flask import request, jsonify, render_template, url_for, g

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
    def convert_image_to_data_url(image_url):
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            # Determine the MIME type from the response headers.
            mime_type = response.headers.get('Content-Type', 'image/jpeg')
            # Encode the image content to base64.
            base64_data = base64.b64encode(response.content).decode('utf-8')
            data_url = f"data:{mime_type};base64,{base64_data}"
            return data_url
        except Exception as e:
            logger.error("Error converting image: %s", e)
            return None

    try:
        user_id = getattr(g, 'user_id', "test_user")
        podcast_doc, status_code = podcast_repo.get_podcast_by_id(user_id, podcast_id)

        if status_code != 200:
            logger.warning(f"⚠️ Podcast {podcast_id} not found!")
            return render_template("404.html")

        episodes_response, status_code = episode_repo.get_episodes_by_podcast(podcast_id, user_id)
        episodes_list = episodes_response.get("episodes", []) if status_code == 200 else []

        social_media_links = map_social_links(podcast_doc.get("podcast", {}).get("socialMedia", []))

        podcast_title = podcast_doc.get("podcast", {}).get("podName", "Default Podcast Title")
        podcast_description = podcast_doc.get("podcast", {}).get("description", "Default Podcast Description")

        # Grab host_name and author_name from the document
        host_name = podcast_doc.get("podcast", {}).get("hostName", "")
        author_name = podcast_doc.get("podcast", {}).get("author", "")

        # If host_name is empty, fall back to author_name
        if not host_name:
            host_name = author_name or "Unknown Host"

        host_bio = podcast_doc.get("podcast", {}).get("hostBio", "No biography available.")
        tagline = podcast_doc.get("podcast", {}).get("tagline", "No tagline available.")

        # Extract banner_url and logoUrl from the document
        banner_url = podcast_doc.get("podcast", {}).get("bannerUrl", "")
        podcast_logo = podcast_doc.get("podcast", {}).get("logoUrl", "")
        host_image = podcast_doc.get("podcast", {}).get("hostImage", "")

        # If no banner_url is provided, fallback to using the podcast_logo
        if not banner_url:
            banner_url = podcast_logo

        # Convert podcast_logo if it's an external URL
        if isinstance(podcast_logo, str):
            if podcast_logo.startswith("data:image"):
                pass  # Already a data URL
            elif podcast_logo.startswith("http"):
                converted_logo = convert_image_to_data_url(podcast_logo)
                if converted_logo:
                    podcast_logo = converted_logo
                else:
                    podcast_logo = url_for('static', filename='images/default.png')
            else:
                podcast_logo = url_for('static', filename='images/default.png')
        else:
            podcast_logo = url_for('static', filename='images/default.png')

        # Convert banner_url if it's an external URL
        if isinstance(banner_url, str):
            if banner_url.startswith("data:image"):
                pass  # Already a data URL
            elif banner_url.startswith("http"):
                converted_banner = convert_image_to_data_url(banner_url)
                if converted_banner:
                    banner_url = converted_banner
                else:
                    banner_url = url_for('static', filename='images/default.png')
            else:
                banner_url = url_for('static', filename='images/default.png')
        else:
            banner_url = url_for('static', filename='images/default.png')

        # Process host_image if needed
        if not isinstance(host_image, str) or not host_image.startswith("data:image"):
            host_image = url_for('static', filename='images/default.png')

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
