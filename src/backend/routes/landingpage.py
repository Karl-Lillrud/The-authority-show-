from flask import g, redirect, render_template, url_for, Blueprint
from backend.database.mongo_connection import get_db  # Add import

landingpage_bp = Blueprint("landingpage_bp", __name__)




@landingpage_bp.route('/landingpage', methods=['GET'])
def landingpage():
    if not g.user_id:
        return redirect(url_for('signin_bp.signin'))

    # Get the database and select the Episodes collection
    db = get_db()
    episodes_collection = db["Episodes"]
    
    # Query for added podcasts. Adjust the query as needed.
    episodes = list(episodes_collection.find({}))
    
    return render_template(
        'landingpage/landingpage.html',
        episodes=episodes
    )


@landingpage_bp.route('/episode', methods=['GET'])
def episode():
    if not g.user_id:
        return redirect(url_for('signin_bp.signin'))
    return render_template('landingpage/episode.html')