from flask import Blueprint, render_template

frontend_bp = Blueprint('frontend', __name__, template_folder='../../Frontend/templates')

@frontend_bp.route('/podprofile')
def podprofile():
    return render_template('podprofile/podprofile.html')
