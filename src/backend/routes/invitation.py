from flask import Blueprint, request, jsonify, render_template, url_for
from backend.utils.email_utils import send_email
import logging

invitation_bp = Blueprint('invitation_bp', __name__)

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@invitation_bp.route('/send_invitation', methods=['POST'])
def send_invitation():
    data = request.get_json()
    logger.info(f"Received data for invitation: {data}")
    email = data.get('email')
    subject = data.get('subject')
    body = render_template('beta-email/podmanager-beta-invite.html')
    if email and subject and body:
        send_email(email, subject, body)
        return jsonify({'success': True})
    logger.error("Missing required fields for sending invitation email.")
    return jsonify({'success': False, 'error': 'Missing required fields'}), 400

@invitation_bp.route('/invite_email_body', methods=['GET'])
def invite_email_body():
    return render_template('beta-email/podmanager-beta-invite.html')
