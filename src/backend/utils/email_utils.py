import smtplib
import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load environment variables once when the module is imported
load_dotenv(override=True)

# Configure logger
logger = logging.getLogger(__name__)

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
        logger.info(f"Sending email to {to_email} via {smtp_server}:{smtp_port}")
        
        with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
            server.set_debuglevel(1)  # Enable debug output
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
            
        logger.info(f"Email sent successfully to {to_email}")
        return True
            
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}", exc_info=True)
        logger.error(f"SMTP settings: Server={smtp_server}, Port={smtp_port}, User={sender_email}")
        return False

def send_team_invite_email(email, invite_token, company_name=None, inviter_name=None):
    """Sends an invitation email for a team membership with registration link."""
    subject = "You've been invited to join a team!"
    
    # Get the base URL from environment, with fallback options
    base_url = os.getenv("PROD_BASE_URL") or "https://app.podmanager.ai"
    
    # Create the registration link with the invite token
    registration_link = f"{base_url}/register_team_member.html?token={invite_token}"
    
    # Optional company name and inviter info
    company_info = f"the team at {company_name}" if company_name else "a team"
    inviter_info = f" by {inviter_name}" if inviter_name else ""
    
    logger.info(f"Preparing invitation email to {email} with link {registration_link}")
    
    body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                <h2 style="color: #0056b3;">Team Invitation</h2>
                <p>Hello,</p>
                <p>You've been invited to join {company_info}{inviter_info}.</p>
                <p>To accept this invitation, please click the button below to register as a team member:</p>
                <p style="text-align: center;">
                    <a href="{registration_link}" style="
                        display: inline-block;
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