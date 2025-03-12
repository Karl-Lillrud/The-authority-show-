from flask import g, redirect, render_template, url_for, Blueprint
from backend.database.mongo_connection import collection  # Add import

landingpage_bp = Blueprint("landingpage_bp", __name__)





@landingpage_bp.route('/landingpage', methods=['GET'])
def landingpage():
    if not g.user_id:
        return redirect(url_for('signin_bp.signin'))
    return render_template('landingpage/landingpage.html')


@landingpage_bp.route('/episode', methods=['GET'])
def episode():
    if not g.user_id:
        return redirect(url_for('signin_bp.signin'))
    return render_template('landingpage/episode.html')