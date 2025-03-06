import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")


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

# Add a new function for guest confirmations
def send_guest_confirmation_email(guest_email, podcast_data):
    subject = f"Podcast Recording Confirmed - {podcast_data['podName']}"
    
    body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2>Your Podcast Recording is Confirmed! 🎙️</h2>
            <p>Hello!</p>
            <p>Your podcast recording has been scheduled successfully.</p>
            
            <div style="background: #f5f5f5; padding: 15px; margin: 20px 0;">
                <h3>Recording Details:</h3>
                <p><strong>Show:</strong> {podcast_data['podName']}</p>
                <p><strong>Date:</strong> {podcast_data['recordingDate']}</p>
                <p><strong>Time:</strong> {podcast_data['recordingTime']}</p>
                <p><strong>Platform:</strong> {podcast_data.get('platform', 'Zoom')}</p>
            </div>
            
            <p><strong>Next Steps:</strong></p>
            <ul>
                <li>Add this event to your calendar</li>
                <li>Review any preparation materials</li>
                <li>Test your equipment before the recording</li>
            </ul>
            
            <p>Questions? Contact us at {podcast_data['hostEmail']}</p>
        </body>
    </html>
    """
    
    send_email(guest_email, subject, body)