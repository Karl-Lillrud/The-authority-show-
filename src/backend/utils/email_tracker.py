import json
import os
import logging

SENT_EPISODES_FILE = "sent_episodes.json"  # JSON file to track sent episodes

# Ensure the sent_episodes.json file exists
if not os.path.exists(SENT_EPISODES_FILE):
    with open(SENT_EPISODES_FILE, "w") as file:
        json.dump({}, file)  # Initialize an empty dictionary

def load_sent_episodes():
    """Load the list of sent episodes (episode IDs)."""
    try:
        with open(SENT_EPISODES_FILE, "r") as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Error loading sent episodes file: {str(e)}")
        return {}

def save_sent_episodes(sent_episodes):
    """Save the list of sent episodes (episode IDs)."""
    try:
        with open(SENT_EPISODES_FILE, "w") as file:
            json.dump(sent_episodes, file)
    except Exception as e:
        logging.error(f"Error saving sent episodes file: {str(e)}")
