import os
import logging
from flask import Blueprint, jsonify

# Configure logger
logger = logging.getLogger(__name__)

# Define Blueprint with a new name
stripe_config_bp = Blueprint("stripe_config_bp", __name__)

@stripe_config_bp.route('/config', methods=['GET']) # Keep the route path as /config for frontend compatibility
def get_config():
    """Exposes necessary public configuration variables to the frontend."""
    try:
        config_data = {
            'apiBaseUrl': os.getenv('API_BASE_URL', ''), # Provide API_BASE_URL
            # --- Corrected to use the PUBLIC key for the frontend ---
            'stripePublicKey': os.getenv('STRIPE_PUBLIC_KEY', '') # Provide STRIPE_PUBLIC_KEY
        }
        # Ensure keys exist in .env
        if not config_data['apiBaseUrl']:
            logger.warning("API_BASE_URL not set in environment variables. Frontend might use relative paths.")
            # Fallback to relative URLs if not set, but log a warning.
        # --- Updated error check and message for the PUBLIC key ---
        if not config_data['stripePublicKey']:
            logger.error("STRIPE_PUBLIC_KEY not set in environment variables. Stripe functionality will fail.")
            # Return an error or empty key if critical
            return jsonify({"error": "Stripe public key not configured on server."}), 500

        return jsonify(config_data), 200
    except Exception as e:
        logger.error(f"Error fetching configuration: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch server configuration"}), 500
