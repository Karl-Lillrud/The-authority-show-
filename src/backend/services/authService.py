import dns
from flask import jsonify
import re
from flask import jsonify

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
    # Check if the email ends with @gmail.com (or any other domain you'd like to verify)
    if email.endswith("@gmail.com"):
        if not check_gmail_existence(email):
            return jsonify({"error": "The provided Gmail address does not exist or is not valid."}), 400
    return None

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
        # Query for MX records
        answers = dns.resolver.resolve(domain, 'MX')
        if answers:
            return True
        else:
            return False
    except Exception as e:
        print(f"MX record lookup failed for domain '{domain}': {e}")
        return False
