import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
import re
import dns.resolver

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))


def send_email(to_email, subject, body):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "html"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, to_email, msg.as_string())
        server.quit()
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")


def check_gmail_existence(email):
    """
    Verifies that the provided email address is valid and that its domain
    is configured to receive emails by checking for MX records.
    This function is not limited to Gmail addresses; it works for any valid email.
    """
    # Validate email format
    email_regex = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    if not re.match(email_regex, email):
        return False

    # Extract domain from email
    try:
        domain = email.split("@")[1]
    except IndexError:
        return False

    # Check for MX records for the domain
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        if answers:
            return True
        else:
            return False
    except Exception as e:
        print(f"MX record lookup failed for domain '{domain}': {e}")
        return False
