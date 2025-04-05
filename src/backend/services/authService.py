import logging
import re
import dns
import random
import time
import hashlib
import pytz
from datetime import datetime, timedelta
from timezonefinder import TimezoneFinder
from flask import jsonify, session
from werkzeug.security import check_password_hash
from backend.database.mongo_connection import collection
from backend.services.teamService import TeamService
from backend.services.accountService import AccountService
from backend.utils.email_utils import send_email

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.user_collection = collection.database.Users
        self.team_service = TeamService()
        self.account_service = AccountService()
    
    def signin(self, data):
        try:
            email = data.get("email", "").strip().lower()
            password = data.get("password", "")
            remember = data.get("remember", False)

            # Authenticate user
            user = self._authenticate_user(email, password)
            if not user:
                return {"error": "Invalid email or password"}, 401
            
            # Set up session
            self._setup_session(user, remember)
            
            # Get user's personal account and teams
            user_id = session["user_id"]
            user_account = self.account_service.get_user_account(user_id)
            team_list = self.team_service.get_user_teams(user_id)
            
            # Determine active account
            active_account = self.account_service.determine_active_account(user_id, user_account, team_list)
            if not active_account:
                return {"error": "No account or team-associated account found"}, 403

            # Prepare response data
            account_id = active_account.get("_id")
            redirect_url = "/podprofile" if user_account else "/podcastmanager"
            
            response = {
                "message": "Login successful",
                "redirect_url": redirect_url,
                "teams": team_list,
                "accountId": str(account_id),
                "isTeamMember": user.get("isTeamMember", False),
                "usingTeamAccount": bool(not user_account and active_account != user_account)
            }

            return response, 200

        except Exception as e:
            logger.error("Error during login: %s", e, exc_info=True)
            return {"error": f"Error during login: {str(e)}"}, 500

    def verify_code_and_login(self, email, code):
        """
        Verifies the provided code and logs in the user if the code is valid.
        """
        try:
            # Fetch the user's stored code and expiration time from the database
            user_data = self.user_collection.find_one({"email": email})
            if not user_data:
                logger.error(f"User with email {email} not found.")
                return {"error": "Email not found"}, 404

            stored_code = user_data.get("verification_code")
            expiration_time = user_data.get("code_expires_at")

            # Check if the code or expiration time is missing
            if not stored_code or not expiration_time:
                logger.error(f"Verification code or expiration time missing for email {email}.")
                return {"error": "Verification code not found or expired"}, 400

            # Check if the code has expired
            if datetime.utcnow() > expiration_time:
                logger.error(f"Verification code for email {email} has expired.")
                return {"error": "Verification code has expired"}, 400

            # Check if the code matches
            if hashlib.sha256(code.encode()).hexdigest() != stored_code:
                logger.error(f"Invalid verification code for email {email}.")
                return {"error": "Invalid verification code"}, 400

            # Remove the code after successful verification
            self.user_collection.update_one(
                {"email": email},
                {"$unset": {"verification_code": "", "code_expires_at": ""}}
            )

            # Log in the user (set up session or return a token)
            user = self.user_collection.find_one({"email": email})
            self._setup_session(user, remember=False)

            logger.info(f"User with email {email} logged in successfully.")
            return {"message": "Login successful", "redirect_url": "/dashboard"}, 200
        except Exception as e:
            logger.error(f"Error verifying code for email {email}: {e}", exc_info=True)
            return {"error": "An error occurred during verification"}, 500

    def send_verification_code(self, email, latitude=None, longitude=None):
        """
        Generate and send a verification code to the user's email.
        Dynamically fetch the timezone based on latitude and longitude.
        """
        try:
            # Generate a 6-digit verification code
            code = str(random.randint(100000, 999999))

            # Determine the timezone based on latitude and longitude
            if latitude is not None and longitude is not None:
                tf = TimezoneFinder()
                timezone_name = tf.timezone_at(lat=latitude, lng=longitude)
                if not timezone_name:
                    timezone_name = "Europe/Stockholm"  # Default to Sweden's timezone if none found
            else:
                timezone_name = "Europe/Stockholm"  # Default to Sweden's timezone if no location is provided

            # Get the current time in the determined timezone (handling DST automatically)
            local_timezone = pytz.timezone(timezone_name)
            current_time = datetime.now(local_timezone)  # Current time in the user's timezone
            expiration_time = datetime.utcnow() + timedelta(minutes=10)  # Extend validity to 10 minutes

            # Hash the verification code
            hashed_code = hashlib.sha256(code.encode()).hexdigest()

            # Store the verification code and expiration time in the database
            self.user_collection.update_one(
                {"email": email},
                {"$set": {"verification_code": hashed_code, "code_expires_at": expiration_time}},
                upsert=True
            )

            # Send the verification code to the user's email
            subject = "Verification Code"
            body = f"Your verification code is: {code}. This code is valid for 10 minutes."
            send_email(email, subject, body)
            logger.info(f"Verification code sent to {email}")
            return {"message": "Verification code sent"}
        except Exception as e:
            logger.error(f"Error sending the verification code to {email}: {e}", exc_info=True)
            return {"error": f"Failed to send verification code: {str(e)}"}

    def _store_verification_code(self, email, hashed_code, expiration_time, created_at):
        """
        Store the hashed verification code and its expiration time in the database.
        """
        # Save to MongoDB (replace with your database logic)
        self.user_collection.update_one(
            {"email": email},
            {
                "$set": {
                    "verification_code": hashed_code,
                    "verification_expiration": expiration_time,  # Expiration time as formatted hours and minutes
                    "createdAt": created_at,  # Time when the button was clicked as formatted hours and minutes
                }
            },
            upsert=True
        )

    def _authenticate_user(self, email, password):
        """Authenticate user with email and password."""
        user = self.user_collection.find_one({"email": email})
        if not user or not check_password_hash(user["passwordHash"], password):
            return None
        return user

    def _setup_session(self, user, remember):
        """Set up user session data."""
        session["user_id"] = str(user["_id"])
        session["email"] = user["email"]
        session.permanent = remember

# Function to validate password
def validate_password(password):
    """
    Validates the password to ensure it is at least 8 characters long and contains 
    at least one letter and one number.
    """
    # Validate password length
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters long."}), 400
    
    # Validate that the password contains at least one letter and one number
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        return jsonify({"error": "Password must contain at least one letter and one number."}), 400
    
    return None  # Return None if validation passes

def validate_email(email):
    """
    Validate email format and check existence via MX records.
    """
    # Validate email format
    email_regex = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    if not re.match(email_regex, email):
        return jsonify({"error": "Invalid email format."}), 400

    # Extract domain from the email
    domain = email.split('@')[1]
    
    # Check for MX records for the domain
    if not check_mx_record(domain):
        return jsonify({"error": f"The provided email domain '{domain}' does not exist or is not valid."}), 400

    return None  # Return None if validation passes

def check_mx_record(domain):
    """
    Verifies that the domain of the email has valid MX records.
    """
    try:
        # Query MX records for the domain
        answers = dns.resolver.resolve(domain, 'MX')
        return bool(answers)  # Return True if MX records are found, else False
    except Exception as e:
        print(f"MX record lookup failed for domain '{domain}': {e}")
        return False  # MX record lookup failed
