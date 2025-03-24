import smtplib
import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage  # Added for inline image support
from dotenv import load_dotenv

# Load environment variables once
load_dotenv(override=True)

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")

# Configure logger
logger = logging.getLogger(__name__)

def send_email(to_email, subject, body, image_path=None):
    """
    Sends an email with optional inline image attachments.
    """
    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = to_email
    msg["Subject"] = subject

    # Attach the HTML content
    msg.attach(MIMEText(body, "html"))

    # 🔹 Attach inline image (PodManagerLogo.png) if available
    if image_path and os.path.exists(image_path):
        try:
            with open(image_path, "rb") as img_file:
                img = MIMEImage(img_file.read(), _subtype="png")
                img.add_header("Content-ID", "<pod_manager_logo>")  # Needed for inline image
                img.add_header("Content-Disposition", "inline", filename="PodManagerLogo.png")
                msg.attach(img)
            logger.info("✅ Attached inline image successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to attach image: {e}")

    try:
        logger.info(f"📡 Connecting to SMTP server {SMTP_SERVER}:{SMTP_PORT}")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        logger.info(f"🔐 Logging in as {EMAIL_USER}")
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, to_email, msg.as_string())
        server.quit()
        logger.info(f"✅ Email successfully sent to {to_email}")
        return {"success": True}
    except Exception as e:
        logger.error(f"❌ Failed to send email to {to_email}: {e}")
        return {"error": str(e)}

def send_team_invite_email(email, invite_token, team_name=None, inviter_name=None, role="Member"):
    """
    Sends an invitation email for a team membership with an inline logo.
    """
    # 🔹 Force LOCALHOST for debugging
    base_url = "http://127.0.0.1:8000"

    # Create the registration link with the invite token, team name, and role
    registration_link = f"{base_url}/register_team_member?token={invite_token}"
    
    # Add team name and role parameters if available
    if team_name:
        registration_link += f"&teamName={team_name}"
    
    # Add role parameter (using default if not provided)
    registration_link += f"&role={role}"

    # ✅ Log the generated URL before sending the email
    logger.info(f"🔗 Forced LOCALHOST invite URL: {registration_link} for {email}")

    subject = "You've been invited to join a team!"
    
    team_info = f"the team at {team_name}" if team_name else "a team"
    inviter_info = f" by {inviter_name}" if inviter_name else ""

    body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; text-align: center;">
                <img src="cid:pod_manager_logo" alt="PodManager Logo" style="max-width: 150px; margin-bottom: 20px;">
                <h2 style="color: #0056b3;">Team Invitation</h2>
                <p>Hello,</p>
                <p>You've been invited to join {team_info}{inviter_info}.</p>
                <p>To accept this invitation, please click the button below to register as a team member:</p>
                <p style="text-align: center;">
                    <a href="{registration_link}" style="display: inline-block;
                        padding: 12px 24px;
                        background-color: #FF8C00;
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

    # Path to the PodManager logo
    image_path = "src/frontend/static/images/PodManagerLogo.png"

    # 🔹 Call send_email() with inline image support
    return send_email(email, subject, body, image_path=image_path)