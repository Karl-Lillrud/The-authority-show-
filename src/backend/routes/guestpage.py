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
    """
    Build a social media dictionary from individual guest fields.
    """
    social_media = {}
    if guest.get("linkedin"):
        social_media["linkedin"] = guest["linkedin"]
    if guest.get("twitter"):
        social_media["twitter"] = guest["twitter"]
    # Add additional social fields if available:
    # if guest.get("instagram"):
    #     social_media["instagram"] = guest["instagram"]
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
        
        # Extract fields from the MongoDB document
        guest_name = guest.get("name", "Default Guest Name")
        guest_bio = guest.get("bio", "Default Guest Biography")
        guest_image = guest.get("image", "")
        podcast_id = guest.get("podcastId", "")
        tags = guest.get("tags", [])
        description = guest.get("description", "")
        email = guest.get("email", "")
        linkedin = guest.get("linkedin", "")
        twitter = guest.get("twitter", "")
        areas_of_interest = guest.get("areasOfInterest", [])
        status = guest.get("status", "")
        scheduled = guest.get("scheduled", 0)
        completed = guest.get("completed", 0)
        created_at = guest.get("created_at", "")

        # Fallback if guest_image is empty or not a valid data URI
        if not isinstance(guest_image, str) or not guest_image.startswith("data:image"):
            guest_image = url_for('static', filename='images/default.png')

        # If you have episodes for the guest
        episodes_response, ep_status_code = guest_repo.get_episodes_by_guest(guest_id)
        if ep_status_code != 200:
            logger.error(f"Failed to fetch episodes for guest {guest_id}: {episodes_response}")
            episodes_list = []
        else:
            episodes_list = episodes_response.get("episodes", [])

        # Render the guestpage template, passing all fields you need
        return render_template(
            "guestpage/guestpage.html",
            guest_name=guest_name,
            guest_bio=guest_bio,
            guest_image=guest_image,
            podcast_id=podcast_id,
            tags=tags,
            description=description,
            email=email,
            linkedin=linkedin,
            twitter=twitter,
            areas_of_interest=areas_of_interest,
            guest_status=status,
            scheduled=scheduled,
            completed=completed,
            created_at=created_at,
            episodes=episodes_list
        )
    except Exception as e:
        logger.error(f"Error loading guest page: {str(e)}")
        return f"Error: {str(e)}", 500

