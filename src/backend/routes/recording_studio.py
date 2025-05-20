from flask import Blueprint, render_template, session, g, redirect, url_for

recording_studio_bp = Blueprint('recording_studio', __name__)

@recording_studio_bp.route('/studio')
def recording_studio():
    if not g.user_id:
        return redirect(url_for('auth.login'))
    return render_template('recordingstudio/recording_studio.html')
