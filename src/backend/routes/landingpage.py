from flask import g, redirect, render_template, url_for, Blueprint
from backend.database.mongo_connection import get_db  # Add import

landingpage_bp = Blueprint("landingpage_bp", __name__)





@landingpage_bp.route('/landingpage', methods=['GET'])
def landingpage():
    if not g.user_id:
        return redirect(url_for('signin_bp.signin'))
    
    db = get_db()
    
    # Query the Podcasts collection for your podcast details.
    podcasts_collection = db["Podcasts"]
    podcast_doc = podcasts_collection.find_one({})  # You can filter if necessary.
    
    # Get podcast title and description from the document.
    podcast_title = podcast_doc.get("podName", "Default Podcast Title") if podcast_doc else "Default Podcast Title"
    podcast_description = podcast_doc.get("description", "Default Podcast Description") if podcast_doc else "Default Podcast Description"
    host_name = podcast_doc.get("hostName", "Error with name") if podcast_doc else "Default Podcast Description"

    
    # You can also still query episodes if needed:
    episodes_collection = db["Episodes"]
    episodes = list(episodes_collection.find({}))
    
    return render_template(
        'landingpage/landingpage.html',
        podcast_title=podcast_title,
        podcast_description=podcast_description,
        episodes=episodes,
        host_name=host_name
    )
@landingpage_bp.route('/episode', methods=['GET'])
def episode():
    if not g.user_id:
        return redirect(url_for('signin_bp.signin'))
    return render_template('landingpage/episode.html')