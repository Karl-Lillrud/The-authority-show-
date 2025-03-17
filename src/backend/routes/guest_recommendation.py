from flask import Blueprint, request, jsonify, render_template
from backend.services.guest_followup_email import send_guest_followup_email

guest_bp = Blueprint("guest_bp", __name__)

@guest_bp.route("/send-guest-followup", methods=["POST"])
def send_guest_followup():
    """Endpoint to send a follow-up email to a guest, asking for recommendations."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    guest_email = data.get("email")
    guest_name = data.get("name", "Guest")

    if not guest_email:
        return jsonify({"error": "Email is required"}), 400

    try:
        send_guest_followup_email(guest_email, guest_name)
        return jsonify({"message": "Follow-up email sent successfully."}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to send follow-up email: {str(e)}"}), 500

@guest_bp.route("/guest-recommendation", methods=["GET", "POST"])
def guest_recommendation():
    """Page where guests can submit their recommendations."""
    if request.method == "GET":
        return render_template("recommendations/guest-recommendation.html")
    else:
        recommendations = request.form.get("recommendations")
        # TODO: Save recommendations to your database
        # e.g., db.save_recommendations(guest_id, recommendations)
        return jsonify({"message": "Thank you for your recommendation!"}), 200
