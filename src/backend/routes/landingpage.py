from flask import g, redirect, render_template, url_for, Blueprint
from backend.database.mongo_connection import get_db  # Import MongoDB connection

landingpage_bp = Blueprint("landingpage_bp", __name__)

@landingpage_bp.route('/landingpage', methods=['GET'])
def landingpage():
    if not g.user_id:
        return redirect(url_for('signin_bp.signin'))
    
    db = get_db()
    podcasts_collection = db["Podcasts"]
    
    # Fetch podcast document
    podcast_doc = podcasts_collection.find_one({})
    
    # Extract details
    podcast_title = podcast_doc.get("podName", "Default Podcast Title") if podcast_doc else "Default Podcast Title"
    podcast_description = podcast_doc.get("description", "Default Podcast Description") if podcast_doc else "Default Podcast Description"
    host_name = podcast_doc.get("hostName", "Unknown Host") if podcast_doc else "Unknown Host"
    if not isinstance(social_media_links, list):
        social_media_links = []
    
    # Handle Podcast Logo (Base64 or Default)
    podcast_logo = ""
    if podcast_doc:
        podcast_logo = podcast_doc.get("logoUrl", "")
        if not podcast_logo.startswith("data:image"):  # Ensure it's Base64
            podcast_logo = url_for('static', filename='images/default.png')

    # Fetch Episodes
    episodes_collection = db["Episodes"]
    episodes = list(episodes_collection.find({}))

    return render_template(
        'landingpage/landingpage.html',
        podcast_title=podcast_title,
        podcast_description=podcast_description,
        podcast_logo=podcast_logo,
        host_name=host_name,
        social_media=social_media_links,  # ✅ Correctly pass social media
        episodes=episodes
    )

@landingpage_bp.route('/episode', methods=['GET'])
def episode():
    if not g.user_id:
        return redirect(url_for('signin_bp.signin'))
    return render_template('landingpage/episode.html')
