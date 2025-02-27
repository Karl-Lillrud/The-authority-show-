from flask import Blueprint, send_from_directory
import os

frontend_bp = Blueprint('frontend', __name__, static_folder='../../Frontend')

@frontend_bp.route('/templates/<path:filename>')
def serve_template(filename):
    return send_from_directory(os.path.join(frontend_bp.static_folder, 'templates'), filename)
