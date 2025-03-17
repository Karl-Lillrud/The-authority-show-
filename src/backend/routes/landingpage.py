from flask import g, redirect, render_template, url_for, Blueprint

from backend.database.mongo_connection import collection, podcasts, get_db  # Add import



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
    try:
        if not hasattr(g, 'user_id'):
            g.user_id = "test_user"
        if not g.user_id:
            return redirect(url_for('signin_bp.signin'))
        return render_template('landingpage/episode.html')
    except Exception as e:
        return f"Error: {str(e)}", 500

@landingpage_bp.route("/landingpage/<podcast_id>")
def landingpage_by_id(podcast_id):
    try:
        podcast = podcasts.find_one({"_id": podcast_id})
          # Debug
        if podcast:
            return render_template("landingpage/landingpage.html", podcast=podcast)
        return render_template("404.html")
    except Exception as e:
        return f"Error: {str(e)}", 500