import os
from flask import render_template_string
from flask_mail import Message
from backend import mail
import logging

# Set up logger
logger = logging.getLogger(__name__)

def send_guest_followup_email(app, recipient_email, recipient_name, email_template):
    """Send follow-up email to the guest."""
    # Ensure Flask app context is available
    try:
        subject = email_template["subject"]
        template_path = email_template["template"]

        # Read the template file manually
        template_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'frontend', 'emails', 'templates')
        template_file_path = os.path.join(template_dir, template_path)

        with open(template_file_path, 'r') as f:
            email_content = f.read()  # Read the email template file as a string

        # Replace placeholders in the email template manually
        email_body = render_template_string(email_content, name=recipient_name)

        msg = Message(subject, recipients=[recipient_email])
        msg.html = email_body  # Use the rendered content
        mail.send(msg)  # Send the email using Flask-Mail
        logger.info(f"Follow-up email sent to {recipient_email}")
    except Exception as e:
        logger.error(f"Error sending email to {recipient_email}: {e}")
