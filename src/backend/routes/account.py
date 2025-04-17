from flask import Blueprint, request, jsonify, g, render_template, session
from backend.repository.account_repository import AccountRepository
from backend.services.accountService import AccountService
import logging

account_bp = Blueprint("account_bp", __name__)
account_service = AccountService()
account_repo = AccountRepository()
logger = logging.getLogger(__name__)


@account_bp.before_request
def populate_user_context():
    if not hasattr(g, "email"):
        g.email = session.get("email")


@account_bp.route("/create_account", methods=["POST"])
def create_account_route():
    try:
        data = request.get_json()
        user_id = data.get("userId")
        email = data.get("email")
        if not user_id or not email:
            return jsonify({"error": "userId och email krävs"}), 400

        account, status_code = account_service.create_account_if_not_exists(
            user_id, email, data.get("isCompany", False), data.get("companyName", "")
        )
        return (
            jsonify(
                {"message": "Konto skapat eller hittat", "accountId": account["_id"]}
            ),
            status_code,
        )
    except Exception as e:
        logger.error(f"Fel vid skapande av konto: {e}", exc_info=True)
        return jsonify({"error": f"Fel vid skapande av konto: {str(e)}"}), 500


@account_bp.route("/get_account", methods=["GET"])
def get_account_route():
    if not hasattr(g, "user_id") or not g.user_id:
        return jsonify({"error": "Obehörig"}), 401

    account = account_service.get_user_account(str(g.user_id))
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
        response, status_code = account_service.update_account(str(g.user_id), data)
        return jsonify(response), status_code
    except Exception as e:
        logger.error(f"Fel vid uppdatering av konto: {e}", exc_info=True)
        return jsonify({"error": f"Fel vid uppdatering av konto: {str(e)}"}), 500


@account_bp.route("/billing", methods=["GET"])
def buy_credits():
    user_id = request.args.get("user_id")
    return render_template("billing/billing.html", user_id=user_id)
