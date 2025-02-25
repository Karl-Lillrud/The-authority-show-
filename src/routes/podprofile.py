from flask import Blueprint, render_template, session

podprofile_bp = Blueprint('podprofile_bp', __name__)

@podprofile_bp.route('/podprofile')
def podprofile():
    user_email = session.get('user_email', '')
    return render_template('podprofile/podprofile.html', user_email=user_email)
