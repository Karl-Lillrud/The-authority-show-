from flask import Blueprint, request, jsonify, g, render_template, session
from backend.models.accounts import AccountSchema
import logging
from backend.repository.account_repository import AccountRepository
from backend.database.mongo_connection import collection


# Define Blueprint
account_bp = Blueprint("account_bp", __name__)

# Instantiate the Account Repository
account_repo = AccountRepository()

# Configure logger
logger = logging.getLogger(__name__)


# Middleware to populate g.email
@account_bp.before_request
def populate_user_context():
    if not hasattr(g, "email"):
        g.email = session.get("email")


@account_bp.route("/create-account", methods=["POST"])
def create_account():
    data = request.get_json()
    user_id = data.get("userId")
    email = data.get("email")

    if not user_id or not email:
        logger.error("Missing userId or email in request")
        return jsonify({"error": "User ID and email are required"}), 400

    try:
        account_data = {"ownerId": user_id, "email": email, "isFirstLogin": True}
        account_result, status_code = account_repo.create_account(account_data)
        if status_code in [200, 201]:
            return (
                jsonify(
                    {
                        "message": "Account created or already exists",
                        "accountId": account_result["accountId"],
                    }
                ),
                status_code,
            )
        else:
            logger.error(
                f"Failed to create account for user {user_id}: {account_result.get('error')}"
            )
            return jsonify({"error": account_result.get("error")}), status_code
    except Exception as e:
        logger.error(
            f"Error creating account for user {user_id}: {str(e)}", exc_info=True
        )
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@account_bp.route("/get_account", methods=["GET"])
def get_account_route():
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Obehörig"}), 401

    account = account_repo.get_account_by_user(str(g.user_id))
    if not account:
        return jsonify({"error": "Konto hittades inte"}), 404

    return jsonify({"account": account}), 200


@account_bp.route("/edit_account", methods=["PUT"])
def edit_account():
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Obehörig"}), 401

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Inga data angivna"}), 400
        response, status_code = account_repo.update_account(str(g.user_id), data)
        return jsonify(response), status_code
    except Exception as e:
        logger.error(f"Fel vid uppdatering av konto: {e}", exc_info=True)
        return jsonify({"error": f"Fel vid uppdatering av konto: {str(e)}"}), 500


@account_bp.route("/billing", methods=["GET"])
def buy_credits():
    user_id = request.args.get("user_id")
    return render_template("billing/billing.html", user_id=user_id)
