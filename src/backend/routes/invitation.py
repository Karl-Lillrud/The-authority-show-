from flask import Blueprint, request, jsonify
from backend.utils.email_utils import send_email

invitation_bp = Blueprint('invitation_bp', __name__)

@invitation_bp.route('/send_invitation', methods=['POST'])
def send_invitation():
    data = request.get_json()
    email = data.get('email')
    subject = data.get('subject')
    body = data.get('body')
    if email and subject and body:
        send_email(email, subject, body)
        return jsonify({'success': True})
    return jsonify({'success': False}), 400
