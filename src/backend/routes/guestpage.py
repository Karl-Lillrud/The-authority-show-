from flask import g, redirect, render_template, url_for, Blueprint
import logging
from backend.repository.guest_repository import GuestRepository
from backend.repository.episode_repository import EpisodeRepository

guestpage_bp = Blueprint("guestpage_bp", __name__)
logger = logging.getLogger(__name__)

# Initialize repositories
guest_repo = GuestRepository()
episode_repo = EpisodeRepository()

def map_social_links_from_fields(guest):
    def ensure_protocol(link):
        if link and not link.startswith("http"):
            return "https://" + link
        return link

    social_media = {}

    twitter = guest.get("twitter", "").strip()
    if twitter:
        twitter_link = ensure_protocol(twitter)
        social_media["twitter"] = twitter_link

    linkedin = guest.get("linkedin", "").strip()
    if linkedin:
        linkedin_link = ensure_protocol(linkedin)
        social_media["linkedin"] = linkedin_link

    return social_media

@guestpage_bp.route("/guestpage/<guest_id>")
def guestpage(guest_id):
    try:
        user_id = getattr(g, 'user_id', "test_user")

        # Fetch the guest document
        guest_response, status_code = guest_repo.get_guest_by_id(user_id, guest_id)
        if status_code != 200:
            logger.warning(f"Guest {guest_id} not found!")
            return render_template("404.html"), 404

        guest = guest_response.get("guest", {})

        # Extract guest image with fallback
        guest_image = guest.get("image", "")
        if not isinstance(guest_image, str) or not guest_image.startswith("data:image"):
            guest_image = url_for('static', filename='images/default.png')

        # Map social media links from the guest document
        social_media = map_social_links_from_fields(guest)

        # Fetch episodes for the guest
        episode_id = guest.get("episodeId")
        episode = {}
        if episode_id:
            episode_data, status = episode_repo.get_episode(episode_id, user_id)
            if status == 200:
                episode = {
                    "_id": episode_data.get("_id"),
                    "title": episode_data.get("title"),
                    "description": episode_data.get("description"),
                    "banner": episode_data.get("imageUrl", "") or url_for('static', filename='images/default_banner.png'),
                }
        episodes_list = [episode] if episode else []

        return render_template(
            "guestpage/guestpage.html",
            guest_name=guest.get("name", "Default Guest Name"),
            guest_bio=guest.get("bio", "Default Guest Biography"),
            guest_image=guest_image,
            podcast_id=guest.get("podcastId", ""),
            tags=guest.get("tags", []),
            description=guest.get("description", ""),
            email=guest.get("email", ""),
            areas_of_interest=guest.get("areasOfInterest", []),
            guest_status=guest.get("status", ""),
            scheduled=guest.get("scheduled", 0),
            completed=guest.get("completed", 0),
            created_at=guest.get("created_at", ""),
            episodes=episodes_list,
            social_media=social_media
        )
    except Exception as e:
        logger.error(f"Error loading guest page: {str(e)}")
        return f"Error: {str(e)}", 500