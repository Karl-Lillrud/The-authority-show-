from flask import Blueprint, request
from pymongo import MongoClient
import os, secrets, smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()
activation_bp = Blueprint("activation", __name__)

client = MongoClient("mongodb://localhost:27017/")
db = client["Podmanager"]
podcasts = db["Podcasts"]

def send_activation_email(email, activation_link, podcast_name, artwork_url):
    html = f"""
    <html>
        <body>
            <p>Hi </p>
            <p>We're thrilled to offer you exclusive early access to <strong>PodManager</strong>, 
            the ultimate tool built to simplify podcasting for creators like you!</p>
            <p>We’ve already prepared your account. Just activate it to start unlocking the full potential of PodManager:</p>
            <p><a href="{activation_link}">Activate Your Account Now</a></p>
        </body>
    </html>
    """
    
    msg = MIMEText(html, "html")
    msg["Subject"] = "Exclusive Access to PodManager—Activate Your Account Today! 🚀"
    msg["From"] = os.getenv("EMAIL")
    msg["To"] = email

    try:
        with smtplib.SMTP("smtp.office365.com", 587) as server:
            server.ehlo()
            server.starttls()  # ✅ Use STARTTLS instead of SSL
            server.ehlo()
            server.login("contact@podmanager.ai", "!Pat9INfeKKpH4Rack8942&")
            server.send_message(msg)
        print(f"✅ Sent to {email}")
    except Exception as e:
        print(f"❌ Email failed: {e}")

@activation_bp.route("/activation/invite", methods=["GET"])
def invite_user():
    email = 'me@karllillrud.com'
    podcast = podcasts.find_one({"emails": email})
    if not podcast:
        return "❌ No podcast found", 404

    # Direct to /signin with query params
    link = f"http://localhost:5000/signin?email={email}"
    send_activation_email(email, link, podcast['title'], podcast.get("artwork_url", ""))
    return f"✅ Invitation sent to {email}"