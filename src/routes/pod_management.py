from flask import render_template, jsonify, Blueprint, g
from database.mongo_connection import collection

"""
Podcast Management Module

This module handles routes for managing podcast-related data, including:
- Loading all guests
- Viewing guest profiles
- Fetching user-created podcasts
"""

# Define Flask Blueprint for podcast management
dashboardmanagement_bp = Blueprint("dashboardmanagement_bp", __name__)


# Load all guests
@dashboardmanagement_bp.route("/load_all_guests", methods=["GET"])
def load_all_guests():

    """Fetches all guests from the database."""
    guests = list(collection.find({"type": "guest"}))
    return jsonify(guests)


# Guest Profile Page
@dashboardmanagement_bp.route("/profile/<guest_id>", methods=["GET"])
def guest_profile(guest_id):

    """Retrieves guest profile information by ID and renders profile page."""
    guests = load_all_guests().get_json()  # Fetches list of guests
    guest = next((g for g in guests if g.get("id") == guest_id), None)
    
    if guest is None:

        return "Guest not found", 404
    
    return render_template("guest/profile.html", guest=guest)


# Get User's Podcasts
@dashboardmanagement_bp.route("/get_user_podcasts", methods=["GET"])
def get_user_podcasts():

    """Fetches all podcasts created by the currently logged-in user."""
    if not g.user_id:
        
        return jsonify({"error": "Unauthorized"}), 401
    
    podcasts = list(collection.find({"creator_id": g.user_id}))
    return jsonify(podcasts)
