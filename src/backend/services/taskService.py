import re #THIS CLASS CAN HELP TO MAKE DEFAULT TASKS INTO REGULAR TASKS "IMPORT"
from flask import Flask, request, jsonify

app = Flask(__name__)

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
    guest_id = request.args.get('guestId')
    if not guest_id:
        return jsonify({"error": "Guest ID is required"}), 400

    # Example data - replace with actual database query
    episodes = [
        {"id": "1", "title": "Episode 1"},
        {"id": "2", "title": "Episode 2"},
        {"id": "3", "title": "Episode 3"}
    ]

    return jsonify(episodes), 200

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)