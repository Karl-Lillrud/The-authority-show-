import logging
import re
import dns.resolver
import random
import hashlib
import uuid
from datetime import datetime, timedelta
from flask import jsonify, session, request, current_app
from werkzeug.security import check_password_hash
from backend.database.mongo_connection import collection
from backend.services.teamService import TeamService
from backend.services.accountService import AccountService
from backend.utils.email_utils import send_login_email
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.user_collection = collection.database.Users
        self.account_service = AccountService()
        self.team_service = TeamService()
        self.account_service.set_team_service(self.team_service)

    def signin(self, data):
        """Hantera inloggning med email och lösenord."""
        try:
            email = data.get("email", "").strip().lower()
            password = data.get("password", "")
            remember = data.get("remember", False)

            user = self._authenticate_user(email, password)
            if not user:
                logger.warning(f"Ogiltig inloggning för email {email}.")
                return {"error": "Ogiltigt email eller lösenord"}, 401

            self._setup_session(user, remember)
            user_id = session["user_id"]

            user_account, status_code = self.account_service.create_account_if_not_exists(
                user_id, email
            )
            if status_code not in [200, 201]:
                logger.error(f"Misslyckades att skapa/hämta konto för {email}: {user_account.get('error')}")
                return {"error": user_account.get('error')}, status_code

            team_list = self.team_service.get_user_teams(user_id)
            active_account = self.account_service.determine_active_account(
                user_id, user_account, team_list
            )
            if not active_account:
                logger.warning(f"Inget aktivt konto för userId {user_id}.")
                return {"error": "Inget konto eller team-associerat konto hittades"}, 403

            redirect_url = "/podprofile" if user_account else "/podcastmanager"
            response = {
                "message": "Inloggning framgångsrik",
                "redirect_url": redirect_url,
                "teams": team_list,
                "accountId": str(active_account["_id"]),
                "isTeamMember": user.get("isTeamMember", False),
                "usingTeamAccount": bool(user_account != active_account),
            }
            return response, 200

        except Exception as e:
            logger.error(f"Fel vid inloggning: {e}", exc_info=True)
            return {"error": f"Fel vid inloggning: {str(e)}"}, 500

    def generate_otp(self, email):
        """Generera och lagra en OTP för en användare."""
        try:
            otp = str(random.randint(100000, 999999))
            hashed_otp = hashlib.sha256(otp.encode()).hexdigest()
            expires_at = datetime.utcnow() + timedelta(minutes=10)

            self.user_collection.update_one(
                {"email": email},
                {"$set": {"otp": hashed_otp, "otp_expires_at": expires_at}},
                upsert=True
            )
            logger.info(f"OTP genererad för email {email}.")
            return otp
        except Exception as e:
            logger.error(f"Fel vid generering av OTP för {email}: {e}", exc_info=True)
            raise

    def verify_otp_and_login(self, email, otp):
        """Verifiera OTP och logga in användaren."""
        try:
            user = self.user_collection.find_one({"email": email})
            if not user:
                logger.warning(f"Användare med email {email} hittades inte.")
                return {"error": "Email hittades inte"}, 404

            hashed_otp = hashlib.sha256(otp.encode()).hexdigest()
            if user.get("otp") != hashed_otp or user.get("otp_expires_at") < datetime.utcnow():
                logger.warning(f"Ogiltig eller utgången OTP för email {email}.")
                return {"error": "Ogiltig eller utgången OTP"}, 401

            self._setup_session(user, False)
            self.user_collection.update_one(
                {"email": email}, {"$unset": {"otp": "", "otp_expires_at": ""}}
            )
            logger.info(f"Användare {email} autentiserad via OTP.")

            user_account, status_code = self.account_service.create_account_if_not_exists(
                user["_id"], email
            )
            if status_code not in [200, 201]:
                logger.error(f"Misslyckades att skapa/hämta konto för {email}: {user_account.get('error')}")
                return {"error": user_account.get('error')}, status_code

            return {"user_authenticated": True, "user": user, "account": user_account}, 200

        except Exception as e:
            logger.error(f"Fel vid OTP-verifiering för email {email}: {e}", exc_info=True)
            return {"error": f"Fel vid autentisering: {str(e)}"}, 500

    def verify_login_token(self, token):
        """Verifiera inloggningstoken och logga in användaren."""
        try:
            serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
            email = serializer.loads(token, salt="login-link-salt", max_age=600)

            user = self.user_collection.find_one({"email": email})
            if not user:
                user_data = {
                    "_id": str(uuid.uuid4()),
                    "email": email,
                    "createdAt": datetime.utcnow().isoformat(),
                }
                logger.debug(f"Skapar ny användare med data: {user_data}")
                self.user_collection.insert_one(user_data)
                user = user_data
                logger.info(f"Ny användare skapad för email {email}.")

            logger.debug(f"Användardata för tokenverifiering: user_id={user['_id']}, email={email}")
            self._setup_session(user, False)

            user_account, status_code = self.account_service.create_account_if_not_exists(
                user["_id"], email
            )
            if status_code not in [200, 201]:
                logger.error(f"Misslyckades att skapa/hämta konto för {email}: {user_account.get('error')}")
                return {"error": f"Misslyckades att skapa konto: {user_account.get('error')}"}, 500

            logger.info(f"Användare {email} inloggad via token.")
            return {"redirect_url": "/podprofile", "account": user_account}, 200

        except SignatureExpired:
            logger.error("Token har gått ut")
            return {"error": "Token har gått ut"}, 400
        except BadSignature:
            logger.error("Ogiltig token")
            return {"error": "Ogiltig token"}, 400
        except Exception as e:
            logger.error(f"Fel vid tokenverifiering: {str(e)}", exc_info=True)
            return {"error": f"Internt serverfel vid tokenverifiering: {str(e)}"}, 500

    def _authenticate_user(self, email, password):
        """Autentisera användare med email och lösenord."""
        try:
            user = self.user_collection.find_one({"email": email})
            if not user or not check_password_hash(user.get("passwordHash", ""), password):
                return None
            return user
        except Exception as e:
            logger.error(f"Fel vid autentisering av användare {email}: {e}", exc_info=True)
            return None

    def _setup_session(self, user, remember):
        """Sätt upp användarsession."""
        try:
            session["user_id"] = str(user["_id"])
            session["email"] = user["email"]
            session.permanent = remember
        except Exception as e:
            logger.error(f"Fel vid uppstart av session för {user['email']}: {e}", exc_info=True)
            raise

    def validate_email(self, email):
        """Validera email-format och MX-record."""
        try:
            email_regex = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
            if not re.match(email_regex, email):
                return {"error": "Ogiltigt email-format."}, 400

            domain = email.split("@")[1]
            answers = dns.resolver.resolve(domain, "MX")
            return None if answers else ({"error": f"Ogiltig email-domän '{domain}'."}, 400)
        except Exception as e:
            logger.error(f"MX-uppslag misslyckades för domän '{domain}': {e}", exc_info=True)
            return {"error": f"Ogiltig email-domän '{domain}'."}, 400

    def validate_password(self, password):
        """Validera lösenord."""
        try:
            if len(password) < 8:
                return {"error": "Lösenordet måste vara minst 8 tecken långt."}, 400
            if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
                return {"error": "Lösenordet måste innehålla både bokstäver och siffror."}, 400
            return None
        except Exception as e:
            logger.error(f"Fel vid validering av lösenord: {e}", exc_info=True)
            return {"error": "Fel vid validering av lösenord."}, 400