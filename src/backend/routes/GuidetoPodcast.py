from flask import Blueprint, render_template

# Define the blueprint
GuidetoPodcast_bp = Blueprint('GuidetoPodcast', __name__)

# Define the route
@GuidetoPodcast_bp.route('/create_podcast')
def show_GuidetoPodcast():
    return render_template('create_podcast/create.html')
