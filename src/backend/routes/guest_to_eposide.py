from flask import request, jsonify, Blueprint, g
from backend.database.mongo_connection import collection, database
from datetime import datetime, timezone
import uuid

guesttoepisode_bp = Blueprint("guesttoepisode_bp", __name__)

#NEED CHANGES ADDED AS EXAMPLE, NOT FINAL. DISPLAY IS THAT "2 GUEST CAN BE ASSIGNED TO 1 EPISODE"
#SHOULD ONLY BE USED FOR SPECIFIC DATA CRUD OPERATIONS
#EXTRA FUNCTIONALITY BESIDES CRUD OPERATIONS SHOULD BE IN SERVICES

# Route to assign a guest to an episode
@guesttoepisode_bp.route('/add-guest-to-episode', methods=['POST'])
def assign_guest():
    data = request.get_json()
    episode_id = data.get('episode_id')
    guest_id = data.get('guest_id')

    if not episode_id or not guest_id:
        return jsonify({"error": "Both episode_id and guest_id are required."}), 400

    # Check if the guest is already assigned to this episode
    existing_assignment = collection.find_one({
        'episode_id': episode_id,
        'guest_id': guest_id
    })
    
    if existing_assignment:
        return jsonify({"error": f"Guest {guest_id} is already assigned to episode {episode_id}."}), 400

    # Assign the guest to the episode
    assignment = {
        'episode_id': episode_id,
        'guest_id': guest_id,
        'assigned_at': datetime.now(timezone.utc)
    }
    
    collection.insert_one(assignment)

    return jsonify({"message": f"Guest {guest_id} assigned to episode {episode_id}."}), 200

# Route to remove a guest from an episode
@guesttoepisode_bp.route('/remove-guest-from-episode', methods=['POST'])
def remove_guest():
    data = request.get_json()
    episode_id = data.get('episode_id')
    guest_id = data.get('guest_id')

    if not episode_id or not guest_id:
        return jsonify({"error": "Both episode_id and guest_id are required."}), 400

    # Remove the guest from the episode
    result = collection.delete_one({
        'episode_id': episode_id,
        'guest_id': guest_id
    })

    if result.deleted_count > 0:
        return jsonify({"message": f"Guest {guest_id} removed from episode {episode_id}."}), 200
    return jsonify({"error": "Failed to remove guest or guest not assigned."}), 400

# Route to get all guests for a specific episode
@guesttoepisode_bp.route('/get-guests-for-episode', methods=['GET'])
def get_guests():
    episode_id = request.args.get('episode_id')
    
    if not episode_id:
        return jsonify({"error": "episode_id is required."}), 400

    # Find all guests assigned to the episode
    assignments = collection.find({'episode_id': episode_id})
    guests = [assignment['guest_id'] for assignment in assignments]
    
    return jsonify({"guests": guests}), 200

# Route to get all episodes for a specific guest
@guesttoepisode_bp.route('/get-episodes-for-guest', methods=['GET'])
def get_episodes():
    guest_id = request.args.get('guest_id')
    
    if not guest_id:
        return jsonify({"error": "guest_id is required."}), 400

    # Find all episodes the guest is assigned to
    assignments = collection.find({'guest_id': guest_id})
    episodes = [assignment['episode_id'] for assignment in assignments]
    
    return jsonify({"episodes": episodes}), 200

# Route to assign a guest to an active podcast
@guesttoepisode_bp.route('/assign-guest-to-active-podcast', methods=['POST'])
def assign_to_active_podcast():
    data = request.get_json()
    guest_id = data.get('guest_id')
    podcast_id = data.get('podcast_id')

    if not guest_id or not podcast_id:
        return jsonify({"error": "Both guest_id and podcast_id are required."}), 400

    # Check if the guest is already active in a podcast
    existing_active_podcast = collection.find_one({
        'guest_id': guest_id,
        'active': True
    })
    
    if existing_active_podcast:
        return jsonify({"error": f"Guest {guest_id} is already active in podcast {existing_active_podcast['podcast_id']}."}), 400

    # Assign the guest to the active podcast
    active_assignment = {
        'guest_id': guest_id,
        'podcast_id': podcast_id,
        'active': True,
        'assigned_at': datetime.now(timezone.utc)
    }
    
    collection.insert_one(active_assignment)

    return jsonify({"message": f"Guest {guest_id} is now active in podcast {podcast_id}."}), 200
