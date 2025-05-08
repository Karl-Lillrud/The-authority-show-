import logging
import re
import dns.resolver
import random
import hashlib
import uuid
import os
from datetime import datetime, timedelta
from flask import jsonify, session, request, current_app
from werkzeug.utils import secure_filename
from backend.database.mongo_connection import collection
from backend.services.teamService import TeamService
from backend.repository.auth_repository import AuthRepository
from backend.repository.account_repository import AccountRepository
from backend.repository.podcast_repository import PodcastRepository
from backend.repository.user_repository import UserRepository
from backend.repository.episode_repository import EpisodeRepository
from backend.services.activity_service import ActivityService
from backend.utils.blob_storage import upload_file_to_blob
from backend.utils.email_utils import send_login_email
from backend.services.rss_Service import RSSService  # Import RSSService
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import time  # Import time for expiration calculation
import jwt  # Import jwt for token generation and verification

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self):
        self.user_collection = collection.database.Users
        self.auth_repository = AuthRepository()
        self.account_repository = AccountRepository()
        self.podcast_repository = PodcastRepository()  # Ensure this is initialized
        self.team_service = TeamService()
        self.user_repo = UserRepository()
        self.episode_repo = EpisodeRepository()
        self.activity_service = ActivityService()
        self.rss_service = RSSService()  # Initialize RSSService

    def signin(self, data):
        """Handle login with email."""
        try:
            email = data.get("email", "").strip().lower()
            remember = data.get("remember", False)

            serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
            token = serializer.dumps(email, salt="login-link-salt")

            # Assuming send_login_email is implemented in email_utils
            login_link = f"{request.host_url.rstrip('/')}/auth/verify-token/{token}"
            send_login_email(email, login_link)

            logger.info(f"Login link sent to {email}")
            return {"message": "Login link sent to your email"}, 200

        except Exception as e:
            logger.error(f"Error during login: {e}", exc_info=True)
            return {"error": f"Login error: {str(e)}"}, 500

    def generate_otp(self, email):
        """Generate and store an OTP for a user."""
        try:
            otp = str(random.randint(100000, 999999))
            hashed_otp = hashlib.sha256(otp.encode()).hexdigest()
            expires_at = datetime.utcnow() + timedelta(minutes=10)

            self.user_collection.update_one(
                {"email": email},
                {"$set": {"otp": hashed_otp, "otp_expires_at": expires_at}},
                upsert=True,
            )
            logger.info(f"OTP generated for email {email}.")
            return otp
        except Exception as e:
            logger.error(f"Error generating OTP for {email}: {e}", exc_info=True)
            raise

    def verify_otp_and_login(self, email, otp):
        """Verify OTP and log in the user."""
        try:
            user = self.auth_repository.find_user_by_email(email)
            if not user:
                logger.warning(f"User with email {email} not found.")
                return {"error": "Email not found"}, 404

            hashed_otp = hashlib.sha256(otp.encode()).hexdigest()
            if (
                user.get("otp") != hashed_otp
                or user.get("otp_expires_at") < datetime.utcnow()
            ):
                logger.warning(f"Invalid or expired OTP for email {email}.")
                return {"error": "Invalid or expired OTP"}, 401

            self._setup_session(user, False)
            self.user_collection.update_one(
                {"email": email}, {"$unset": {"otp": "", "otp_expires_at": ""}}
            )
            logger.info(f"User {email} authenticated via OTP.")

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
                    f"Failed to create/retrieve account for {email}: {account_result.get('error')}"
                )
                return {"error": account_result.get("error")}, status_code

            return {
                "user_authenticated": True,
                "user": user,
                "accountId": account_result["accountId"],
            }, 200

        except Exception as e:
            logger.error(f"Error verifying OTP for {email}: {e}", exc_info=True)
            return {"error": f"Authentication error: {str(e)}"}, 500

    def verify_login_token(self, token):
        """Verify login token and log in the user."""
        try:
            serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
            email = serializer.loads(token, salt="login-link-salt", max_age=600)

            # Use the new helper method to find or create user
            user = self._find_or_create_user(email)
            if not user:
                return {"error": "Failed to authenticate user"}, 500

            logger.debug(
                f"User data for token verification: user_id={user['_id']}, email={email}"
            )
            self._setup_session(user, True)  # Set remember=True for email login

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
                    f"Failed to create/retrieve account for {email}: {account_result.get('error')}"
                )
                return {
                    "error": f"Failed to create account: {account_result.get('error')}"
                }, status_code

            logger.info(f"User {email} logged in via token.")

            podcast_data, status_code = self.podcast_repository.get_podcasts(
                user.get("_id")
            )
            podcasts = podcast_data.get("podcast", [])
            redirect_url = "/podcastmanagement" if podcasts else "/podprofile"

            return {
                "redirect_url": redirect_url,
                "accountId": account_result["accountId"],
            }, 200

        except SignatureExpired:
            logger.error("Token has expired")
            return {"error": "Token has expired"}, 400
        except BadSignature:
            logger.error("Invalid token")
            return {"error": "Invalid token"}, 400
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}", exc_info=True)
            return {
                "error": f"Internal server error during token verification: {str(e)}"
            }, 500

    def _find_or_create_user(self, email):
        """Find user by email or create if not exists."""
        try:
            user = self.auth_repository.find_user_by_email(email)
            if not user:
                user_data = {
                    "_id": str(uuid.uuid4()),
                    "email": email,
                    "createdAt": datetime.utcnow().isoformat(),
                }
                logger.debug(f"Creating new user with data: {user_data}")
                user = self.auth_repository.create_user(user_data)
                if not user:
                    logger.error(f"Failed to create new user for email {email}")
                    return None
            return user
        except Exception as e:
            logger.error(f"Error finding or creating user {email}: {e}", exc_info=True)
            return None

    def _setup_session(self, user, remember):
        """Set up user session."""
        try:
            session["user_id"] = str(user["_id"])
            session["email"] = user["email"]
            session.permanent = remember
        except Exception as e:
            logger.error(
                f"Error setting up session for {user['email']}: {e}", exc_info=True
            )
            raise

    def validate_email(self, email):
        """Validate email format and MX record."""
        try:
            email_regex = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
            if not re.match(email_regex, email):
                return {"error": "Invalid email format."}, 400

            domain = email.split("@")[1]
            answers = dns.resolver.resolve(domain, "MX")
            return (
                None
                if answers
                else ({"error": f"Invalid email domain '{domain}'."}, 400)
            )
        except Exception as e:
            logger.error(f"MX lookup failed for domain '{domain}': {e}", exc_info=True)
            return {"error": f"Invalid email domain '{domain}'."}, 400

    def get_account_by_user(self, user_id):
        """Retrieve account information by user ID."""
        try:
            response, status_code = self.account_repository.get_account_by_user(user_id)
            if status_code == 200:
                self.activity_service.log_activity(
                    user_id=user_id,
                    activity_type="account_viewed",
                    description="Viewed account details",
                    details={"accountId": response.get("account", {}).get("_id")},
                )
            return response, status_code
        except Exception as e:
            logger.error(
                f"Error retrieving account for user {user_id}: {e}", exc_info=True
            )
            return {"error": f"Internal server error: {str(e)}"}, 500

    def edit_account(self, user_id, data):
        """Update account information."""
        try:
            response, status_code = self.account_repository.edit_account(user_id, data)
            if status_code == 200:
                self.activity_service.log_activity(
                    user_id=user_id,
                    activity_type="account_updated",
                    description="Updated account details",
                    details={"updatedFields": list(data.keys())},
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
        """Delete an account and associated data."""
        try:
            podcasts_response, podcasts_status = self.podcast_repository.get_podcasts(
                user_id
            )
            if podcasts_status == 200:
                for podcast in podcasts_response.get("podcasts", []):
                    delete_podcast_response, delete_podcast_status = (
                        self.podcast_repository.delete_podcast(user_id, podcast["_id"])
                    )
                    if delete_podcast_status != 200:
                        logger.warning(
                            f"Could not delete podcast {podcast['_id']} during account deletion for user {user_id}"
                        )

            deleted_account_count = self.account_repository.delete_by_user(user_id)
            if deleted_account_count == 0:
                logger.warning(
                    f"No account document found to delete for user {user_id}"
                )

            user_response, user_status = self.user_repo.delete_user(user_id)
            if user_status != 200:
                logger.error(
                    f"Failed to delete user document for user {user_id}: {user_response.get('error')}"
                )
                return {"error": "Failed to fully delete user data"}, 500

            self.activity_service.log_activity(
                user_id=user_id,
                activity_type="account_deleted",
                description="User account deleted",
                details={},
            )

            return {"message": "Account and associated data deleted successfully"}, 200

        except Exception as e:
            logger.error(
                f"Error deleting account for user {user_id}: {e}", exc_info=True
            )
            return {
                "error": f"Internal server error during account deletion: {str(e)}"
            }, 500

    def upload_profile_picture(self, user_id, file):
        """Upload a profile picture to Azure Blob Storage and update the account."""
        try:
            if not file or not file.filename:
                return {"error": "Invalid file provided"}, 400

            filename = secure_filename(file.filename)
            container_name = "podmanagerfiles"
            blob_path = f"user/{user_id}/profilepicture/{filename}"

            file_url = upload_file_to_blob(container_name, blob_path, file)

            if not file_url:
                return {"error": "Failed to upload profile picture"}, 500

            update_data = {"profilePicUrl": file_url}
            response, status_code = self.edit_account(user_id, update_data)

            if status_code == 200:
                return {
                    "message": "Profile picture updated successfully",
                    "profilePicUrl": file_url,
                }, 200
            else:
                logger.error(
                    f"DB update failed after uploading profile picture for user {user_id}. Blob URL: {file_url}"
                )
                return response, status_code

        except Exception as e:
            logger.error(
                f"Error uploading profile picture for user {user_id}: {e}",
                exc_info=True,
            )
            return {"error": f"Internal server error during upload: {str(e)}"}, 500

    def generate_activation_token(self, email, rss_url, podcast_title, secret_key):
        """Generate an activation token."""
        payload = {
            "email": email,
            "rss_url": rss_url,
            "podcast_title": podcast_title,
            "exp": datetime.utcnow() + timedelta(hours=24),  # Token expires in 24 hours
        }
        return jwt.encode(payload, secret_key, algorithm="HS256")

    def verify_activation_token(self, token):
        """Verify the activation token."""
        try:
            secret_key = current_app.config.get("SECRET_KEY")
            if not secret_key:
                logger.error("SECRET_KEY is not configured in the application for JWT decoding.")
                return None
            return jwt.decode(token, secret_key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            logger.error("Activation JWT has expired.")
            return None
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid activation JWT: {e}")
            return None

    def process_activation_token(self, token):
        """
        Activates a user account via a JWT activation token, logs them in,
        parses their RSS feed, and creates their podcast profile.
        """
        try:
            token_data = self.verify_activation_token(token)
            if not token_data:
                return {"error": "Invalid or expired activation link"}, 400

            email = token_data.get("email")
            rss_url = token_data.get("rss_url")
            podcast_title_from_token = token_data.get("podcast_title")

            if not email or not rss_url:
                logger.error("Invalid JWT token data: Missing email or rss_url")
                return {"error": "Invalid activation token data"}, 400

            logger.info(f"Attempting activation for email: {email}, RSS: {rss_url} using JWT.")

            # 1. Find or Create User
            user = self._find_or_create_user(email)
            if not user:
                logger.error(f"Failed to find or create user during activation for {email}")
                return {"error": "Failed to authenticate user"}, 500
            user_id = user["_id"]  # This is Users._id

            # 2. Log the user in (Setup Session)
            self._setup_session(user, True)

            # 3. Ensure Account Exists
            account_data_for_creation = {
                "ownerId": user_id,  # user_id from Users collection
                "email": email,
                "isFirstLogin": False,  # Activation implies they are now set up
            }
            account_result, status_code = self.account_repository.create_account(account_data_for_creation)
            if status_code not in [200, 201]:
                logger.error(f"Failed to create/retrieve account for {email} during activation: {account_result.get('error')}")
                return {"error": f"Account setup failed: {account_result.get('error')}"}, status_code

            actual_account_id = account_result.get("accountId")  # This is Accounts._id
            if not actual_account_id:
                logger.error(f"accountId not found in account_result for {email} during activation.")
                return {"error": "Failed to retrieve account ID during activation"}, 500
            
            logger.info(f"Account {actual_account_id} ensured for user {user_id} ({email}).")

            # 4. Fetch and Parse RSS Feed
            logger.info(f"Fetching RSS feed for activation: {rss_url}")
            rss_data, rss_status_code = self.rss_service.fetch_rss_feed(rss_url)
            if rss_status_code != 200:
                logger.error(f"Failed to fetch or parse RSS feed {rss_url} during activation: {rss_data.get('error')}")
                return {
                    "message": f"Logged in, but could not fetch podcast data: {rss_data.get('error')}",
                    "redirect_url": "/podprofile",
                }, 200

            # 5. Create Podcast Profile
            logger.info(f"Creating podcast profile for user {user_id}, account {actual_account_id} from RSS: {rss_url}")
            podcast_title = rss_data.get("title", podcast_title_from_token or "Untitled Podcast")
            podcast_creation_data = {
                "accountId": actual_account_id,  # Pass the Accounts._id
                "title": podcast_title,  # This will be used for podName too
                "description": rss_data.get("description"),
                "rssFeed": rss_url,  # Use rssFeed to be consistent with PodcastSchema
                "websiteUrl": rss_data.get("link"),
                "artworkUrl": rss_data.get("imageUrl"),  # This can be mapped to logoUrl
                "language": rss_data.get("language"),
                "author": rss_data.get("author"),
                "ownerName": rss_data.get("itunesOwner", {}).get("name"),
                "ownerEmail": rss_data.get("itunesOwner", {}).get("email"),
                "categories": [
                    cat.get("main") for cat in rss_data.get("categories", []) if cat.get("main")
                ],
                "isImported": True,
                "episodes": rss_data.get("episodes", []),
            }

            create_podcast_result, create_status_code = (
                self.podcast_repository.create_podcast(podcast_creation_data)
            )

            if create_status_code not in [200, 201]:
                logger.error(
                    f"Failed to create podcast profile for user {user_id}, RSS {rss_url}. Result: {create_podcast_result}"  # Modified to log full result
                )
                return {
                    "message": f"Logged in, but failed to create podcast profile: {create_podcast_result.get('error')}",
                    "redirect_url": "/podprofile",
                }, 200

            podcast_id = create_podcast_result.get("podcast", {}).get("_id")
            logger.info(f"✅ Successfully activated user {email} and created podcast {podcast_id}")

            # 6. Log Activation Activity
            self.activity_service.log_activity(
                user_id=user_id,
                activity_type="user_activated_via_link",
                description=f"User account activated via email link for podcast: {podcast_title}",
                details={"email": email, "rss_url": rss_url, "podcast_id": str(podcast_id)},
                ip_address=request.remote_addr if request else None,
            )

            # 7. Return success and redirect URL
            return {
                "message": "Activation successful! Your podcast has been imported.",
                "redirect_url": "/podcastmanagement",
            }, 200

        except Exception as e:
            logger.error(f"Activation token processing error: {str(e)}", exc_info=True)
            return {"error": f"Internal server error during activation: {str(e)}"}, 500
