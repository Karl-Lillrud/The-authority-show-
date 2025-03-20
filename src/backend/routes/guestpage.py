from flask import g, redirect, render_template, url_for, Blueprint
import logging
from backend.repository.guest_repository import GuestRepository
from backend.repository.episode_repository import EpisodeRepository  # If you need other methods

guestpage_bp = Blueprint("guestpage_bp", __name__)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR)

# Initialize repositories
guest_repo = GuestRepository()
# If you have a method in EpisodeRepository to fetch episodes for a guest,
# otherwise, we'll use guest_repo.get_episodes_by_guest
episode_repo = EpisodeRepository()

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
                break
        social_media_dict[matched_platform] = link
    return social_media_dict

@guestpage_bp.route("/guestpage/<guest_id>")
def guestpage(guest_id):
    try:
        # Retrieve user_id (for example, from the session)
        user_id = getattr(g, 'user_id', "test_user")

        # Fetch the guest document from GuestRepository
        guest_doc, status_code = guest_repo.get_guest_by_id(user_id, guest_id)
        if status_code != 200:
            logger.warning(f"Guest {guest_id} not found!")
            return render_template("404.html"), 404

        # Extract guest information
        guest_data = guest_doc.get("guest", {})
        guest_name = guest_data.get("name", "Default Guest Name")
        guest_bio = guest_data.get("bio", "Default Guest Biography")
        guest_image = guest_data.get("image", "")
        if not isinstance(guest_image, str) or not guest_image.startswith("data:image"):
            guest_image = url_for('static', filename='images/default-guest.png')

        # Convert social media links (if stored in the guest document)
        social_links = guest_data.get("socialMedia", [])
        social_media_links = map_social_links(social_links)

        # Fetch episodes in which the guest has participated.
        # Here we use guest_repo.get_episodes_by_guest if you have implemented that method.
        episodes_response, status_code = guest_repo.get_episodes_by_guest(guest_id)
        if status_code != 200:
            logger.error(f"Failed to fetch episodes for guest {guest_id}: {episodes_response}")
            episodes_list = []
        else:
            episodes_list = episodes_response.get("episodes", [])

        # Render a template similar to the landing page (you can adjust the design to resemble LinkedIn if desired)
        return render_template(
            "guestpage/guestpage.html",
            guest_name=guest_name,
            guest_bio=guest_bio,
            guest_image=guest_image,
            social_media=social_media_links,
            episodes=episodes_list
        )
    except Exception as e:
        logger.error(f"Error loading guest page: {str(e)}")
        return f"Error: {str(e)}", 500