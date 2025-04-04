import re #THIS CLASS CAN HELP TO MAKE DEFAULT TASKS INTO REGULAR TASKS "IMPORT"
from flask import Flask, request, jsonify
from pymongo import MongoClient

app = Flask(__name__)

# MongoDB connection setup
client = MongoClient("mongodb://localhost:27017/")
db = client["podcast_manager"]
episodes_collection = db["episodes"]

def extract_highlights(description):
    # Example logic to extract key highlights from the description
    highlights = []
    sentences = re.split(r'(?<=[.!?]) +', description)
    for sentence in sentences:
        if "important" in sentence.lower() or "key" in sentence.lower():
            highlights.append(sentence)
    return highlights 

def process_default_tasks(data):
    # Ensure defaultTasks is None if it's an empty list
    if "defaultTasks" in data and isinstance(data["defaultTasks"], list):
        if len(data["defaultTasks"]) == 0:
            data["defaultTasks"] = None
        else:
            # Save defaultTasks as regular tasks to episodes
            data["tasks"] = data["defaultTasks"]
            data["defaultTasks"] = None
    return data

@app.route('/api/episodes', methods=['GET'])
def get_episodes():
    print("GET /api/episodes called")  # Debug log
    guest_id = request.args.get('guestId')
    if not guest_id:
        print("Guest ID is missing")  # Debug log
        return jsonify({"error": "Guest ID is required"}), 400

    # Fetch episodes from the database
    episodes = list(episodes_collection.find({"guestId": guest_id}, {"_id": 0}))
    if not episodes:
        print(f"No episodes found for guest ID: {guest_id}")  # Debug log
        return jsonify({"message": "No episodes found for this guest"}), 404

    print(f"Found episodes for guest ID: {guest_id}")  # Debug log
    return jsonify(episodes), 200

@app.errorhandler(404)
def not_found_error(error):
    print("404 Error: Endpoint not found")  # Debug log
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    print("500 Error: Internal server error")  # Debug log
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    print("Starting Flask app...")  # Debug log
    app.run(host='127.0.0.1', port=8000, debug=True)