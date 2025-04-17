import uuid
from datetime import datetime
from flask import request, session, redirect, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from backend.database.mongo_connection import collection
from backend.services.authService import AuthService
from backend.repository.usertoteam_repository import UserToTeamRepository
from backend.repository.team_repository import TeamRepository
import logging

logger = logging.getLogger(__name__)


class AuthRepository:
    def __init__(self):
        self.user_collection = collection.database.Users
        self.account_collection = collection.database.Accounts
        self.invite_collection = collection.database.Invites
        self.user_to_team_repo = UserToTeamRepository()
        self.team_repo = TeamRepository()
        self.auth_service = AuthService()

    def signin(self, data):
        return self.auth_service.signin(data)

    def register(self, data):
        try:
            email = data.get("email", "").lower().strip()
            password = data.get("password", "")
            if not email or not password:
                return {"error": "Email och lösenord krävs"}, 400

            email_error = self.auth_service.validate_email(email)
            if email_error:
                return email_error

            password_error = self.auth_service.validate_password(password)
            if password_error:
                return password_error

            if self.user_collection.find_one({"email": email}):
                return {"error": "Email redan registrerad"}, 409

            user_id = str(uuid.uuid4())
            hashed_password = generate_password_hash(password)
            user_document = {
                "_id": user_id,
                "email": email,
                "passwordHash": hashed_password,
                "createdAt": datetime.utcnow().isoformat(),
            }
            self.user_collection.insert_one(user_document)

            account, status_code = (
                self.auth_service.account_service.create_account_if_not_exists(
                    user_id,
                    email,
                    data.get("isCompany", False),
                    data.get("companyName", ""),
                )
            )
            if status_code not in [200, 201]:
                self.user_collection.delete_one({"_id": user_id})
                return {"error": "Misslyckades att skapa konto"}, 500

            return {
                "message": "Registrering framgångsrik",
                "userId": user_id,
                "accountId": account["_id"],
                "redirect_url": url_for("auth_bp.signin", _external=True),
            }, 201

        except Exception as e:
            logger.error(f"Fel vid registrering: {e}", exc_info=True)
            return {"error": f"Fel vid registrering: {str(e)}"}, 500

    def register_team_member(self, data):
        try:
            invite_token = data.get("inviteToken")
            if not invite_token:
                return {"error": "Inbjudningstoken krävs"}, 400

            invite = self.invite_collection.find_one({"_id": invite_token})
            if not invite or invite.get("status") != "pending":
                return {"error": "Ogiltig eller redan använd inbjudan"}, 400

            email = data.get("email", "").lower().strip()
            if invite["email"].lower() != email:
                return {"error": "Email matchar inte inbjudan"}, 400

            if self.user_collection.find_one({"email": email}):
                return {"error": "Email redan registrerad"}, 409

            required_fields = ["password", "fullName", "phone"]
            for field in required_fields:
                if field not in data or not data[field]:
                    return {"error": f"Fältet {field} krävs"}, 400

            user_id = str(uuid.uuid4())
            hashed_password = generate_password_hash(data["password"])
            user_document = {
                "_id": user_id,
                "email": email,
                "passwordHash": hashed_password,
                "fullName": data["fullName"],
                "phone": data["phone"],
                "isTeamMember": True,
                "createdAt": datetime.utcnow().isoformat(),
            }
            self.user_collection.insert_one(user_document)

            user_to_team_data = {
                "userId": user_id,
                "teamId": invite["teamId"],
                "role": invite.get("role"),
            }
            add_result, status_code = self.user_to_team_repo.add_user_to_team(
                user_to_team_data
            )
            if status_code != 201:
                self.user_collection.delete_one({"_id": user_id})
                return {"error": "Misslyckades att lägga till användare i team"}, 500

            self.invite_collection.update_one(
                {"_id": invite_token},
                {
                    "$set": {
                        "status": "accepted",
                        "acceptedAt": datetime.utcnow().isoformat(),
                    }
                },
            )
            return {
                "message": "Teammedlem registrerad framgångsrikt",
                "userId": user_id,
                "redirect_url": url_for("auth_bp.signin", _external=True),
            }, 201

        except Exception as e:
            logger.error(f"Fel vid registrering av teammedlem: {e}", exc_info=True)
            return {"error": f"Fel vid registrering: {str(e)}"}, 500

    def logout(self):
        session.clear()
        response = redirect(url_for("auth_bp.signin"))
        response.delete_cookie("remember_me")
        return response
