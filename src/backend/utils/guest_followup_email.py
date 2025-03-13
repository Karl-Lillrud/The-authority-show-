from flask import url_for, render_template
from .email_utils import send_email
import logging

# Set up logger
logger = logging.getLogger(__name__)

def send_guest_followup_email(app, guest_email, guest_name):
    subject = "We'd Love Your Recommendations!"
    try:
        # Use Flask app context to avoid "Working outside of application context" error
        with app.app_context():
            email_body = render_template(
                "recommendations/guest_followup.html",
                guest_name=guest_name,
                recommendation_link=url_for("guest_bp.guest_recommendation", _external=True)
            )
        
        # Send email
        send_email(guest_email, subject, email_body)
        logger.info(f"Follow-up email sent successfully to {guest_email}")

    except Exception as e:
        logger.error(f"Failed to send follow-up email to {guest_email}. Error: {str(e)}")
        raise

