from flask import g, redirect, render_template, url_for, Blueprint
from backend.database.mongo_connection import collection, podcasts # Add import

landingpage_bp = Blueprint("landingpage_bp", __name__)





@landingpage_bp.route('/landingpage', methods=['GET'])
def landingpage():
    try:
        # Temporary fallback for g.user_id
        if not hasattr(g, 'user_id'):
            g.user_id = "test_user"  # Replace with real auth logic later
        if not g.user_id:
            return redirect(url_for('signin_bp.signin'))
        
        podcasts = list(collection.Podmanager.Podcasts.find())
        return render_template('landingpage/landingpage.html', podcasts=podcasts)
    except Exception as e:
        return f"Error: {str(e)}", 500

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