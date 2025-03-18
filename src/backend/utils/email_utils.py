import smtplib
import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load environment variables once
load_dotenv(override=True)

# Configure logger
logger = logging.getLogger(__name__)

def send_email(to_email, subject, body):
    """
    Sends an email using SMTP with environment-based configuration.
    """
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASS")
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")

    if not sender_email or not sender_password or not smtp_server or not smtp_port:
        logger.error("❌ Missing required SMTP configuration.")
        return False

    # Create email message
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    try:
        logger.info(f"📤 Connecting to SMTP server {smtp_server}:{smtp_port}")
        logger.info(f"📧 Logging in as {sender_email}")

        with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())

        logger.info(f"✅ Email sent successfully to {to_email}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("❌ SMTP Authentication Error: Check EMAIL_USER and EMAIL_PASS")
    except smtplib.SMTPException as e:
        logger.error(f"❌ SMTP Error: {str(e)}", exc_info=True)
    except Exception as e:
        logger.error(f"❌ Unexpected Error: {str(e)}", exc_info=True)

    return False


def send_team_invite_email(email, invite_token, team_name=None, inviter_name=None):
    """
    Sends an invitation email for a team membership.
    Force localhost for debugging to ensure correct URL.
    """
    # 🔹 Force LOCALHOST when running locally
    base_url = "http://127.0.0.1:8000"  # ⚠️ Hardcoded for debugging

    # Create the registration link with the invite token
    registration_link = f"{base_url}/register_team_member?token={invite_token}"

    # ✅ Log the generated URL before sending the email
    logger.info(f"🔗 Forced LOCALHOST invite URL: {registration_link} for {email}")

    subject = "You've been invited to join a team!"
    
    team_info = f"the team at {team_name}" if team_name else "a team"
    inviter_info = f" by {inviter_name}" if inviter_name else ""

    body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                <h2 style="color: #0056b3;">Team Invitation</h2>
                <p>Hello,</p>
                <p>You've been invited to join {team_info}{inviter_info}.</p>
                <p>To accept this invitation, please click the button below to register as a team member:</p>
                <p style="text-align: center;">
                    <a href="{registration_link}" style="display: inline-block;
                        padding: 12px 24px;
                        background-color: #007bff;
                        color: white;
                        text-decoration: none;
                        border-radius: 5px;
                        font-weight: bold;">
                        Register as Team Member
                    </a>
                </p>
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                    <p style="font-size: 14px; color: #666;">
                        If you did not expect this invitation, you can safely ignore this email.
                    </p>
                    <p style="font-size: 14px; color: #666;">
                        This invitation link will expire in 48 hours.
                    </p>
                </div>
            </div>
        </body>
    </html>
    """
    return send_email(email, subject, body)
