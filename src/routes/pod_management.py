from flask import render_template, jsonify, Blueprint, g
from database.cosmos_connection import container

dashboardmanagement_bp = Blueprint('dashboardmanagement_bp', __name__)

@dashboardmanagement_bp.route('/profile/<guest_id>', methods=['GET'])
def guest_profile(guest_id):
    # Replace this with your actual data retrieval logic,
    # for example, querying your database or another data source.
    guests = load_all_guests()  # This should return a list/dictionary of guest info.
    guest = next((g for g in guests if g["id"] == guest_id), None)
    if guest is None:
        return "Guest not found", 404
    return render_template('guest/profile.html', guest=guest)

@dashboardmanagement_bp.route('/get_user_podcasts', methods=['GET'])
def get_user_podcasts():
    if not g.user_id:
        return jsonify({"error": "Unauthorized"}), 401
    query = "SELECT * FROM c WHERE c.creator_id = @user_id"
    parameters = [{"name": "@user_id", "value": g.user_id}]
    podcasts = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
    return jsonify(podcasts)
