import logging
import re
import dns
from flask import jsonify, session
from werkzeug.security import check_password_hash
from backend.database.mongo_connection import collection
from backend.services.teamService import TeamService
from backend.services.accountService import AccountService

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
