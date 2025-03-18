import smtplib
import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
import logging

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")

logger = logging.getLogger(__name__)

# Log environment variables for debugging (do not log sensitive information in production)
logger.info(f"EMAIL_USER: {EMAIL_USER}")  # Added log
logger.info(f"SMTP_SERVER: {SMTP_SERVER}")  # Added log
logger.info(f"SMTP_PORT: {SMTP_PORT}")  # Added log


def send_email(to_email, subject, body):
    """
    Sends a generic email using configuration from environment variables.
    Works with various email providers including Gmail, Outlook/Hotmail, etc.
    """
    # Get email configuration from environment variables
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASS")
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    
    # Validate required environment variables
    missing = [var for var, val in {
        "EMAIL_USER": sender_email,
        "EMAIL_PASS": sender_password,
        "SMTP_SERVER": smtp_server,
        "SMTP_PORT": smtp_port
    }.items() if not val]
    
    if missing:
        error_msg = f"Missing email configuration: {', '.join(missing)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Create email message
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))
    
    try:
        logger.info(f"Connecting to SMTP server {SMTP_SERVER}:{SMTP_PORT}")  # Added log
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        logger.info(f"Logging in as {EMAIL_USER}")  # Added log
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, to_email, msg.as_string())
        server.quit()
        logger.info(f"Email sent to {to_email}")  # Added log
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")  # Added log
