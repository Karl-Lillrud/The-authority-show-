from flask import Blueprint, request, jsonify
from backend.services.accountService import AccountService
import logging

account_bp = Blueprint("account_bp", __name__)
account_service = AccountService()
logger = logging.getLogger(__name__)


@account_bp.route("/create-account", methods=["POST"])
def create_account():
    data = request.get_json()
    user_id = data.get("userId")
    email = data.get("email")

    if not user_id or not email:
        logger.error("Missing userId or email in request")
        return jsonify({"error": "User ID and email are required"}), 400

    try:
        account, status_code = account_service.create_account_if_not_exists(
            user_id, email
        )
        if status_code in [200, 201]:
            return (
                jsonify(
                    {"message": "Account created or already exists", "account": account}
                ),
                status_code,
            )
        else:
            logger.error(
                f"Failed to create account for user {user_id}: {account.get('error')}"
            )
            return jsonify({"error": account.get("error")}), status_code
    except Exception as e:
        logger.error(
            f"Error creating account for user {user_id}: {str(e)}", exc_info=True
        )
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


# Övriga rutter i account_bp...
