import dns.resolver  # Added to correctly use dns resolver
from flask import jsonify
import re

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
