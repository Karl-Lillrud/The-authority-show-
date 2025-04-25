import os
import logging
from flask import Blueprint, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logger
logger = logging.getLogger(__name__)

# Define Blueprint with a new name
stripe_config_bp = Blueprint("stripe_config_bp", __name__)

@stripe_config_bp.route('/config', methods=['GET']) # Keep the route path as /config for frontend compatibility
def get_config():
    """
    Provides necessary frontend configuration like Stripe keys and API URLs.
    """
    # Add log to check if the route is hit
    logger.info("--- Request received for /config route ---") 
    try:
        stripe_public_key = os.getenv('STRIPE_PUBLIC_KEY')
        api_base_url = os.getenv('API_BASE_URL') # Ensure this is set in your .env
        
        # Add logs to check retrieved values
        logger.info(f"Stripe Public Key: {'Found' if stripe_public_key else 'Not Found'}")
        logger.info(f"API Base URL: {api_base_url or 'Not Set'}")

        if not stripe_public_key:
            # Log this error server-side as well
            logger.error("STRIPE_PUBLIC_KEY is not set in environment variables.")
            return jsonify({"error": "Server configuration error: Missing Stripe key."}), 500

        response_data = {
            'stripePublicKey': stripe_public_key,
            'apiBaseUrl': api_base_url or '' # Return empty string if not set, frontend handles it
        }
        logger.info(f"--- Responding to /config with: {response_data} ---")
        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"Error fetching configuration: {e}", exc_info=True)
        return jsonify({"error": f"Internal server error fetching configuration: {str(e)}"}), 500
