from flask import Blueprint, request, jsonify, render_template, url_for, g
from backend.utils.email_utils import send_email
from backend.database.mongo_connection import collection
from backend.models.podcasts import PodcastSchema
from datetime import datetime, timezone
import uuid
import logging

invitation_bp = Blueprint('invitation_bp', __name__)

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@invitation_bp.route('/send_invitation', methods=['POST'])
def send_invitation():
    data = request.get_json()
    logger.info(f"Received data for invitation: {data}")
    email = data.get('email', "").strip()
    subject = data.get('subject', "").strip()
    pod_name = data.get('podName', "").strip()
    pod_rss = data.get('podRss', "").strip()

    if not email or not subject or not pod_name or not pod_rss:
        logger.error("Missing required fields for sending invitation email.")
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    try:
        # Fetch the account document from MongoDB for the logged-in user
        user_account = collection.database.Accounts.find_one({"userId": g.user_id})
        if not user_account:
            logger.error("No account associated with this user")
            return jsonify({"error": "No account associated with this user"}), 403

        # Fetch the account ID that the user already has (do not override with a new one)
        if "id" in user_account:
            account_id = user_account["id"]
        else:
            account_id = str(user_account["_id"])
        logger.info(f"Found account {account_id} for user {g.user_id}")

        # Create the podcast document with the accountId from the account document
        podcast_id = str(uuid.uuid4())
        podcast_item = {
            "_id": podcast_id,
            "accountId": account_id,
            "podName": pod_name,
            "rssFeed": pod_rss,
            "email": email,
            "created_at": datetime.now(timezone.utc),
        }

        # Insert the podcast document into the database
        logger.info(f"Inserting podcast into database: {podcast_item}")
        result = collection.database.Podcasts.insert_one(podcast_item)

        if not result.inserted_id:
            logger.error("Failed to add podcast to the database")
            return jsonify({"error": "Failed to add podcast to the database."}), 500

        # Send the invitation email
        body = render_template('beta-email/podmanager-beta-invite.html')
        send_email(email, subject, body)
        logger.info("Invitation email sent successfully")
        return jsonify({'success': True, 'message': 'Podcast added and invitation email sent successfully'}), 201

    except Exception as e:
        logger.error(f"Failed to add podcast or send invitation email: {e}")
        return jsonify({'success': False, 'error': f"Failed to add podcast or send invitation email: {str(e)}"}), 500

@invitation_bp.route('/invite_email_body', methods=['GET'])
def invite_email_body():
    return render_template('beta-email/podmanager-beta-invite.html')
