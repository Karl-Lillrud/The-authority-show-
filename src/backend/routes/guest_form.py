from flask import Blueprint, request, jsonify, render_template
from backend.repository.guest_repository import GuestRepository
from backend.utils.email_utils import send_guest_invitation
import logging

logger = logging.getLogger(__name__)


guest_form_bp = Blueprint("guest_form", __name__)
logger = logging.getLogger(__name__)

@guest_form_bp.route("/", methods=["GET", "POST"])
def guest_form():
    if request.method == 'POST':
        data = request.get_json()

        try:
            guest_data = {
                "name": data.get("name"),
                "email": data.get("email"),
                "company": data.get("company"),
                "phone": data.get("phone"),
                "bio": data.get("bio"),
                "description": data.get("bio"),
                "tags": [],
                "areasOfInterest": data.get("interest", "").split(','),
                "linkedin": extract_social_link(data.get("socialMedia"), "LinkedIn"),
                "twitter": extract_social_link(data.get("socialMedia"), "Twitter"),
                "image": data.get("imageData"),
                "episodeId": data.get("episodeId"),  # <-- important for invitation
                "status": "Pending",
            }

            repo = GuestRepository()
            result, status = repo.add_guest(guest_data, user_id="guest-form")

            # ✅ Send invite email if episodeId is provided
            if guest_data["episodeId"] and guest_data["email"]:
                try:
                    result = send_guest_invitation({
                        "name": guest_data["name"],
                        "email": guest_data["email"],
                        "episodeId": guest_data["episodeId"]
                    })
                    logger.info(f"✅ Invitation email sent result: {result}")
                except Exception as e:
                    logger.error(f"❌ Failed to send invite email: {e}")

            return jsonify({"message": "Guest form submitted successfully!"}), status

        except Exception as e:
            print("❌ Error handling guest form:", e)
            return jsonify({"error": "Failed to submit form"}), 500

    return render_template('guest-form/guest-form.html')


@guest_form_bp.route("/api/send-invite", methods=["POST"])
def api_send_guest_invite():
    logger.info("📩 /api/send-invite was called!")
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing data"}), 400

    try:
        result = send_guest_invitation(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


