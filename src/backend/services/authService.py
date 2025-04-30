import logging
import re
import dns.resolver
import random
import hashlib
import uuid
import os  # Import os for path manipulation
from datetime import datetime, timedelta
from flask import jsonify, session, request, current_app
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename  # Import for filename sanitization
from backend.database.mongo_connection import collection
from backend.services.teamService import TeamService
from backend.repository.auth_repository import AuthRepository
from backend.repository.account_repository import AccountRepository
from backend.repository.podcast_repository import PodcastRepository
from backend.repository.user_repository import UserRepository
from backend.repository.episode_repository import EpisodeRepository
from backend.services.activity_service import ActivityService
from backend.utils.blob_storage import upload_file_to_blob  # Import the blob storage utility function
from backend.utils.email_utils import send_login_email
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self):
        self.user_collection = collection.database.Users
        self.auth_repository = AuthRepository()
        self.account_repository = AccountRepository()
        self.podcast_repository = PodcastRepository()
        self.team_service = TeamService()
        self.user_repo = UserRepository()
        self.episode_repo = EpisodeRepository()
        self.activity_service = ActivityService()

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

            account_data = {"ownerId": user_id, "email": email, "isFirstLogin": True}
            account_result, status_code = self.account_repository.create_account(
                account_data
            )
            if status_code not in [200, 201]:
                logger.error(
                    f"Misslyckades att skapa/hämta konto för {email}: {account_result.get('error')}"
                )
                return {"error": account_result.get("error")}, status_code

            team_list = self.team_service.get_user_teams(user_id)
            active_account_id = account_result["accountId"]
            active_account = self.account_repository.get_account(active_account_id)[0][
                "account"
            ]

            redirect_url = "/podprofile"
            response = {
                "message": "Inloggning framgångsrik",
                "redirect_url": redirect_url,
                "teams": team_list,
                "accountId": str(active_account_id),
                "isTeamMember": user.get("isTeamMember", False),
                "usingTeamAccount": False,  # Simplify for now
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
                upsert=True,
            )
            logger.info(f"OTP genererad för email {email}.")
            return otp
        except Exception as e:
            logger.error(f"Fel vid generering av OTP för {email}: {e}", exc_info=True)
            raise

    def verify_otp_and_login(self, email, otp):
        """Verifiera OTP och logga in användaren."""
        try:
            user = self.auth_repository.find_user_by_email(email)
            if not user:
                logger.warning(f"Användare med email {email} hittades inte.")
                return {"error": "Email hittades inte"}, 404

            hashed_otp = hashlib.sha256(otp.encode()).hexdigest()
            if (
                user.get("otp") != hashed_otp
                or user.get("otp_expires_at") < datetime.utcnow()
            ):
                logger.warning(f"Ogiltig eller utgången OTP för email {email}.")
                return {"error": "Ogiltig eller utgången OTP"}, 401

            self._setup_session(user, False)
            self.user_collection.update_one(
                {"email": email}, {"$unset": {"otp": "", "otp_expires_at": ""}}
            )
            logger.info(f"Användare {email} autentiserad via OTP.")

            account_data = {
                "ownerId": user["_id"],
                "email": email,
                "isFirstLogin": True,
            }
            account_result, status_code = self.account_repository.create_account(
                account_data
            )
            if status_code not in [200, 201]:
                logger.error(
                    f"Misslyckades att skapa/hämta konto för {email}: {account_result.get('error')}"
                )
                return {"error": account_result.get("error")}, status_code

            return {
                "user_authenticated": True,
                "user": user,
                "accountId": account_result["accountId"],
            }, 200

        except Exception as e:
            logger.error(
                f"Fel vid OTP-verifiering för email {email}: {e}", exc_info=True
            )
            return {"error": f"Fel vid autentisering: {str(e)}"}, 500

    def verify_login_token(self, token):
        """Verifiera inloggningstoken och logga in användaren."""
        try:
            serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
            email = serializer.loads(token, salt="login-link-salt", max_age=600)

            user = self.auth_repository.find_user_by_email(email)
            if not user:
                user_data = {
                    "_id": str(uuid.uuid4()),
                    "email": email,
                    "createdAt": datetime.utcnow().isoformat(),
                }
                logger.debug(f"Skapar ny användare med data: {user_data}")
                user = self.auth_repository.create_user(user_data)
                if not user:
                    logger.error(
                        f"Misslyckades att skapa ny användare för email {email}"
                    )
                    return {"error": "Misslyckades att skapa användare"}, 500

            logger.debug(
                f"Användardata för tokenverifiering: user_id={user['_id']}, email={email}"
            )
            self._setup_session(user, False)

            account_data = {
                "ownerId": user["_id"],
                "email": email,
                "isFirstLogin": True,
            }
            account_result, status_code = self.account_repository.create_account(
                account_data
            )
            if status_code not in [200, 201]:
                logger.error(
                    f"Misslyckades att skapa/hämta konto för {email}: {account_result.get('error')}"
                )
                return {
                    "error": f"Misslyckades att skapa konto: {account_result.get('error')}"
                }, status_code

            logger.info(f"Användare {email} inloggad via token.")

            podcast_data, status_code = self.podcast_repository.get_podcasts(user.get("_id"))
            podcasts = podcast_data.get("podcast", [])
            if podcasts:
                redirect_url = "/podcastmanagement"
            else:
                redirect_url = "/podprofile"

            return {
                "redirect_url": redirect_url,
                "accountId": account_result["accountId"],
            }, 200

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
            user = self.auth_repository.find_user_by_email(email)
            if not user or not check_password_hash(
                user.get("passwordHash", ""), password
            ):
                return None
            return user
        except Exception as e:
            logger.error(
                f"Fel vid autentisering av användare {email}: {e}", exc_info=True
            )
            return None

    def _setup_session(self, user, remember):
        """Sätt upp användarsession."""
        try:
            session["user_id"] = str(user["_id"])
            session["email"] = user["email"]
            session.permanent = remember
        except Exception as e:
            logger.error(
                f"Fel vid uppstart av session för {user['email']}: {e}", exc_info=True
            )
            raise

    def validate_email(self, email):
        """Validera email-format och MX-record."""
        try:
            email_regex = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
            if not re.match(email_regex, email):
                return {"error": "Ogiltigt email-format."}, 400

            domain = email.split("@")[1]
            answers = dns.resolver.resolve(domain, "MX")
            return (
                None
                if answers
                else ({"error": f"Ogiltig email-domän '{domain}'."}, 400)
            )
        except Exception as e:
            logger.error(
                f"MX-uppslag misslyckades för domän '{domain}': {e}", exc_info=True
            )
            return {"error": f"Ogiltig email-domän '{domain}'."}, 400

    def validate_password(self, password):
        """Validera lösenord."""
        try:
            if len(password) < 8:
                return {"error": "Lösenordet måste vara minst 8 tecken långt."}, 400
            if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
                return {
                    "error": "Lösenordet måste innehålla både bokstäver och siffror."
                }, 400
            return None
        except Exception as e:
            logger.error(f"Fel vid validering av lösenord: {e}", exc_info=True)
            return {"error": "Fel vid validering av lösenord."}, 400

    def get_account_by_user(self, user_id):
        """Hämtar kontoinformation baserat på användar-ID."""
        try:
            response, status_code = self.account_repository.get_account_by_user(user_id)
            if status_code == 200:
                self.activity_service.log_activity(
                    user_id=user_id,
                    activity_type="account_viewed",
                    description="Viewed account details",
                    details={"accountId": response.get("account", {}).get("_id")}
                )
            return response, status_code
        except Exception as e:
            logger.error(f"Fel vid hämtning av konto för användare {user_id}: {e}", exc_info=True)
            return {"error": f"Internt serverfel: {str(e)}"}, 500

    def edit_account(self, user_id, data):
        """Uppdaterar kontoinformation."""
        try:
            response, status_code = self.account_repository.edit_account(user_id, data)
            if status_code == 200:
                self.activity_service.log_activity(
                    user_id=user_id,
                    activity_type="account_updated",
                    description="Updated account details",
                    details={"updatedFields": list(data.keys())}
                )
            return response, status_code
        except Exception as e:
            logger.error(f"Fel vid uppdatering av konto för användare {user_id}: {e}", exc_info=True)
            return {"error": f"Internt serverfel: {str(e)}"}, 500
    
    def edit_increment_account(self, user_id, data):
        # Updating account information by increment.
        try:
            response, status_code = self.account_repository.edit_increment_account(user_id, data)
            if status_code == 200:
                self.activity_service.log_activity(
                    user_id=user_id,
                    activity_type="account_updated",
                    description="Updated account details",
                    details={"updatedFields": list(data.keys())}
                )
            return response, status_code
        except Exception as e:
            logger.error(f"Error updating account by user {user_id}: {e}", exc_info=True)
            return {"error": f"Error updating account: {str(e)}"}, 500

    def delete_account(self, user_id):
        """Tar bort ett konto och associerad data."""
        try:
            podcasts_response, podcasts_status = self.podcast_repository.get_podcasts(user_id)
            if podcasts_status == 200:
                for podcast in podcasts_response.get("podcasts", []):
                    delete_podcast_response, delete_podcast_status = self.podcast_repository.delete_podcast(user_id, podcast['_id'])
                    if delete_podcast_status != 200:
                        logger.warning(f"Could not delete podcast {podcast['_id']} during account deletion for user {user_id}")

            deleted_account_count = self.account_repository.delete_by_user(user_id)
            if deleted_account_count == 0:
                logger.warning(f"No account document found to delete for user {user_id}")

            user_response, user_status = self.user_repo.delete_user(user_id)
            if user_status != 200:
                logger.error(f"Failed to delete user document for user {user_id}: {user_response.get('error')}")
                return {"error": "Failed to fully delete user data"}, 500

            self.activity_service.log_activity(
                user_id=user_id,
                activity_type="account_deleted",
                description="User account deleted",
                details={}
            )

            return {"message": "Account and associated data deleted successfully"}, 200

        except Exception as e:
            logger.error(f"Fel vid borttagning av konto för användare {user_id}: {e}", exc_info=True)
            return {"error": f"Internt serverfel under kontoborttagning: {str(e)}"}, 500

    def upload_profile_picture(self, user_id, file):
        """Laddar upp en profilbild till Azure Blob Storage och uppdaterar kontot."""
        try:
            if not file or not file.filename:
                return {"error": "Invalid file provided"}, 400

            # Sanitize the filename
            filename = secure_filename(file.filename)
            # Define container and blob path structure
            container_name = "podmanagerfiles"
            # Construct the blob path: user/<user_id>/profilepicture/<filename>
            blob_path = f"user/{user_id}/profilepicture/{filename}"

            # Use the imported utility function to upload the file
            file_url = upload_file_to_blob(container_name, blob_path, file)

            if not file_url:
                # upload_file_to_blob logs the error, just return a generic message
                return {"error": "Failed to upload profile picture"}, 500

            # Update the account document with the new profile picture URL
            update_data = {"profilePicUrl": file_url}
            # Use the existing edit_account method (which uses account_repository)
            response, status_code = self.edit_account(user_id, update_data)

            if status_code == 200:
                # Log activity (already handled within edit_account if successful)
                # Return the URL in the response
                return {"message": "Profile picture updated successfully", "profilePicUrl": file_url}, 200
            else:
                # If DB update failed, ideally, we might want to delete the uploaded blob.
                # For now, just return the error from edit_account.
                logger.error(f"DB update failed after uploading profile picture for user {user_id}. Blob URL: {file_url}")
                return response, status_code

        except Exception as e:
            # Catch potential exceptions from upload_file_to_blob or edit_account
            logger.error(f"Error uploading profile picture for user {user_id}: {e}", exc_info=True)
            return {"error": f"Internal server error during upload: {str(e)}"}, 500
