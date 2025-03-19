import smtplib
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
    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
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
