import logging
from datetime import datetime, timedelta
import jwt
import os
from flask import current_app, session
from backend.repository.email_change_repository import EmailChangeRepository
from backend.repository.auth_repository import AuthRepository
from backend.utils.email_utils import send_email
from backend.services.authService import AuthService

logger = logging.getLogger(__name__)

class EmailChangeService:
    def __init__(self):
        self.email_change_repo = EmailChangeRepository()
        self.auth_repo = AuthRepository()
        self.auth_service = AuthService()

    def initiate_email_change(self, user_id, current_email, new_email):
        """Initiate the email change process."""
        try:
            logger.info(f"Initiating email change for user {user_id} from {current_email} to {new_email}")
            
            # Validate the new email format and MX record
            validation_result = self.auth_service.validate_email(new_email)
            if validation_result and validation_result[1] != 200:
                logger.warning(f"Email validation failed for {new_email}")
                return validation_result

            # Check if new email is already in use
            existing_user = self.auth_repo.find_user_by_email(new_email)
            if existing_user:
                logger.warning(f"Email {new_email} is already in use")
                return {"error": "Email address is already in use"}, 400

            # Create email change request
            request_result, status_code = self.email_change_repo.create_request(
                user_id, current_email, new_email
            )
            if status_code != 201:
                logger.error(f"Failed to create email change request: {request_result}")
                return request_result, status_code

            request_id = request_result["requestId"]
            logger.info(f"Created email change request {request_id}")

            # Generate confirmation token for new email
            confirm_token = self._generate_email_change_token(request_id, "confirm")

            # Get the base URL from environment variables
            base_url = os.getenv('API_BASE_URL') or os.getenv('LOCAL_BASE_URL', 'http://127.0.0.1:8000')
            base_url = base_url.rstrip('/')

            # Send confirmation email to new address
            confirm_link = f"{base_url}/email/confirm/{confirm_token}"
            self._send_confirmation_email(new_email, confirm_link)

            logger.info(f"Email change process initiated successfully for user {user_id}")
            return {"message": "Email change initiated successfully"}, 200

        except Exception as e:
            logger.error(f"Error initiating email change: {e}", exc_info=True)
            return {"error": f"Internal server error: {str(e)}"}, 500

    def confirm_email_change(self, token):
        """Confirm email change with token."""
        try:
            logger.info("Processing email change confirmation")
            # Verify token
            payload = self._verify_email_change_token(token)
            if not payload or payload.get("action") != "confirm":
                logger.warning("Invalid or expired token for email confirmation")
                return {"error": "Invalid or expired token"}, 400

            request_id = payload.get("request_id")
            request_result, status_code = self.email_change_repo.get_pending_request(request_id)
            if status_code != 200:
                logger.error(f"Failed to get pending request: {request_result}")
                return request_result, status_code

            request = request_result["request"]
            logger.info(f"Found pending request: {request_id}")

            # Update user's email
            user = self.auth_repo.find_user_by_email(request["currentEmail"])
            if not user:
                logger.error(f"User not found for email {request['currentEmail']}")
                return {"error": "User not found"}, 404

            # Update user's email in database
            update_result = self.auth_repo.user_collection.update_one(
                {"_id": user["_id"]},
                {"$set": {
                    "email": request["newEmail"],
                    "updatedAt": datetime.utcnow().isoformat()
                }}
            )

            if update_result.modified_count == 0:
                logger.error(f"Failed to update email for user {user['_id']}")
                return {"error": "Failed to update email"}, 500

            # Mark request as completed
            complete_result, complete_status = self.email_change_repo.complete_request(request_id)
            if complete_status != 200:
                logger.warning(f"Failed to mark request as completed: {complete_result}")

            # Clear all sessions for the user
            self._invalidate_user_sessions(user["_id"])

            logger.info(f"Email change completed successfully for user {user['_id']}")
            return {
                "message": "Email changed successfully. Please log in with your new email.",
                "redirect_url": "/signin"
            }, 200

        except Exception as e:
            logger.error(f"Error confirming email change: {e}", exc_info=True)
            return {"error": f"Internal server error: {str(e)}"}, 500

    def _generate_email_change_token(self, request_id, action):
        """Generate a JWT token for email change confirmation."""
        payload = {
            "request_id": request_id,
            "action": action,
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")

    def _verify_email_change_token(self, token):
        """Verify the email change token."""
        try:
            return jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            logger.error("Email change token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid email change token: {e}")
            return None

    def _send_confirmation_email(self, new_email, confirm_link):
        """Send confirmation email to new address."""
        subject = "Confirm your new email address"
        body = f"""
        Please confirm your new email address by clicking the link below:
        
        {confirm_link}
        
        This link will expire in 24 hours.
        
        If you didn't request this change, please ignore this email.
        """
        send_email(new_email, subject, body)
        logger.info(f"Confirmation email sent to {new_email}")

    def _invalidate_user_sessions(self, user_id):
        """Invalidate all sessions for the user."""
        if session.get("user_id") == user_id:
            logger.info(f"Clearing session for user {user_id}")
            session.clear() 