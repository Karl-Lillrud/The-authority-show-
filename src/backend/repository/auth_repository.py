import uuid
from datetime import datetime, timedelta, timezone
from flask import request, session, redirect, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from backend.database.mongo_connection import collection
from backend.services.authService import validate_password, validate_email
from backend.repository.account_repository import AccountRepository
from backend.repository.usertoteam_repository import UserToTeamRepository
from backend.repository.team_repository import TeamRepository
from backend.repository.podcast_repository import PodcastRepository
from backend.repository.episode_repository import EpisodeRepository
import logging
import dns.resolver  # Ensure dnspython is properly imported

logger = logging.getLogger(__name__)


class AuthRepository:
    def __init__(self):
        self.user_collection = collection.database.Users
        self.account_collection = collection.database.Accounts
        self.podcast_collection = collection.database.Podcasts
        self.invite_collection = collection.database.Invites
        self.user_to_team_repo = UserToTeamRepository()
        self.account_repo = AccountRepository()
        self.teams_collection = collection.database.Teams
        self.users_to_teams_collection = collection.database.UsersToTeams
        self.team_repo = TeamRepository()
        self.podcast_repo = PodcastRepository()
        self.episode_repo = EpisodeRepository()

    def signin(self, data):
        try:
            email = data.get("email", "").strip().lower()
            password = data.get("password", "")
            remember = data.get("remember", False)

            # Validate credentials
            user = self._authenticate_user(email, password)
            if not user:
                return {"error": "Invalid email or password"}, 401

            # Set up user session
            self._setup_session(user, remember)

            # Ensure account exists for the user
            user_account = self.account_collection.find_one({"userId": str(user["_id"])})
            if not user_account:
                account_data = {
                    "id": str(uuid.uuid4()),
                    "userId": str(user["_id"]),
                    "email": email,
                    "created_at": datetime.utcnow(),
                    "isActive": True,
                }
                self.account_collection.insert_one(account_data)

            return {"redirect_url": "/podprofile"}, 200
        except Exception as e:
            logger.error(f"Error during sign-in: {e}", exc_info=True)
            return {"error": "An error occurred during sign-in"}, 500

    def _authenticate_user(self, email, password):
        """Authenticate user with email and password."""
        user = self.user_collection.find_one({"email": email})
        if not user or not check_password_hash(user["passwordHash"], password):
            return None
        return user

    def _setup_session(self, user, remember):
        """Set up user session data."""
        session["user_id"] = str(user["_id"])
        session["email"] = user["email"]
        session.permanent = remember

    def _get_user_teams(self, user_id):
        """Get teams that the user is a member of."""
        team_membership, status_code = self.user_to_team_repo.get_teams_for_user(
            user_id
        )
        teams = team_membership.get("teams", []) if status_code == 200 else []
        logger.info(f"✅ User is part of teams: {teams}")
        return teams

    def _determine_active_account(self, user_account, team_list):
        """Determine which account to use - personal or team."""
        # If user has personal account, use it
        if user_account:
            return user_account

        # If no personal account but user is in teams, try to use team account
        if not team_list:
            return None

        first_team = team_list[0]
        team_id = first_team.get("_id")
        logger.info(f"🔹 First team details: {first_team}")
        logger.info(f"🔹 Team ID: {team_id}")

        # Try to find team owner's account first
        owner_account = self._find_team_owner_account(team_id)
        if owner_account:
            return owner_account

        # Fallback: try to find any team member's account
        return self._find_any_team_member_account(team_id)

    def _find_team_owner_account(self, team_id):
        """Find the account of the team owner."""
        team_owner_mapping = self.users_to_teams_collection.find_one(
            {"teamId": team_id, "role": "creator"}, {"userId": 1}
        )

        if not team_owner_mapping:
            logger.warning(f"⚠️ No creator found for team ID: {team_id}")
            return None

        owner_id = team_owner_mapping.get("userId")
        logger.info(f"🔹 Found team owner ID: {owner_id}")

        owner_account = self.account_collection.find_one({"userId": owner_id})
        if owner_account:
            logger.info(f"🔹 Found account for team owner: {owner_account['_id']}")
            return owner_account
        else:
            logger.warning(f"⚠️ No account found for team owner with ID: {owner_id}")
            return None

    def _find_any_team_member_account(self, team_id):
        """Find any team member's account as fallback."""
        any_team_member = self.users_to_teams_collection.find_one(
            {"teamId": team_id}, {"userId": 1}
        )

        if not any_team_member:
            return None

        member_id = any_team_member.get("userId")
        logger.info(f"🔹 Found team member ID: {member_id}")

        member_account = self.account_collection.find_one({"userId": member_id})
        if member_account:
            logger.info(f"🔹 Found account for team member: {member_account['_id']}")
            return member_account

        return None

    def logout(self):
        session.clear()
        response = redirect(url_for("auth_bp.signin"))
        response.delete_cookie("remember_me")
        return response

    def register(self, data):
        try:
            if "email" not in data or "password" not in data:
                return {"error": "Missing email or password"}, 400

            email = data["email"].lower().strip()
            password = data["password"]

            email_error = validate_email(email)
            if email_error:
                return email_error

            password_error = validate_password(password)
            if password_error:
                return password_error

            if self.user_collection.find_one({"email": email}):
                return {"error": "Email already registered."}, 409

            # Kontrollera om ett konto redan finns för e-postadressen
            existing_account = self.account_collection.find_one({"email": email})
            if existing_account:
                logger.warning(f"Account already exists for email {email}.")
                return {"error": "Account already exists for this email."}, 400

            user_id = str(uuid.uuid4())
            hashed_password = generate_password_hash(password)

            user_document = {
                "_id": user_id,
                "email": email,
                "passwordHash": hashed_password,
                "createdAt": datetime.utcnow().isoformat(),
            }

            self.user_collection.insert_one(user_document)

            account_data = {
                "userId": user_id,
                "email": email,
                "companyName": data.get("companyName", ""),
                "isCompany": data.get("isCompany", False),
            }

            account_response, status_code = self.account_repo.create_account(
                account_data
            )

            if status_code != 201:
                return {
                    "error": "Failed to create account",
                    "details": account_response,
                }, 500

            account_id = account_response["accountId"]

            return {
                "message": "Registration successful!",
                "userId": user_id,
                "accountId": account_id,
                "redirect_url": url_for("auth_bp.signin", _external=True),
            }, 201

        except Exception as e:
            logger.error("Error during registration: %s", e, exc_info=True)
            # Check if the error response needs to be JSON serializable
            error_message = f"Error during registration: {str(e)}"
            status_code = 500
            if (
                isinstance(e, ValueError)
                and len(e.args) > 1
                and isinstance(e.args[1], dict)
            ):
                # Handle validation errors more gracefully if needed
                error_message = e.args[0]
                status_code = 400  # Or appropriate status code
            elif "duplicate key" in str(e).lower():  # Basic check for duplicate errors
                error_message = "An account related error occurred. Please try again or contact support."  # More generic message

            return {"error": error_message}, status_code

    def register_team_member(self, data):
        try:
            logger.info("🔹 Received registration data: %s", data)  # Debug log
            invite_token = data.get("inviteToken")
            if not invite_token:
                logger.error("❌ Missing invite token")  # Debug log
                raise ValueError("Missing invite token")

            # Fetch invite details
            invite = self.invite_collection.find_one({"_id": invite_token})
            if not invite:
                logger.error(f"❌ Invalid invite token: {invite_token}")  # Debug log
                raise ValueError("Invalid invite token")

            # Ensure role is present in the invite
            role = invite.get("role")
            if not role:
                logger.error(f"❌ Missing role in invite: {invite}")  # Debug log
                raise KeyError("role")  # Explicitly raise KeyError if role is missing

            logger.info("✅ Role extracted from invite: %s", role)  # Debug log

            required_fields = ["email", "password", "fullName", "phone"]
            for field in required_fields:
                if field not in data or not data[field]:
                    logger.error(f"❌ Missing required field: {field}")  # Debug log
                    return {"error": f"Missing required field: {field}"}, 400

            email = data["email"].lower().strip()
            password = data["password"]

            # Validate invite status
            if invite.get("status") != "pending":
                logger.error(f"❌ Invite is not pending: {invite}")  # Debug log
                return {"error": "Invite is not valid or already used."}, 400

            # Validate email matches the invite
            if invite["email"].lower() != email:
                logger.error(
                    f"❌ Email mismatch! Invited: {invite['email']} - Registering: {email}"
                )  # Debug log
                return {"error": "The email does not match the invitation."}, 400

            # Check if the email is already registered
            existing_user = self.user_collection.find_one({"email": email})
            if existing_user:
                logger.error("❌ Email already exists: %s", email)  # Debug log
                return {"error": "Email already registered."}, 409

            # Proceed with user registration
            user_id = str(uuid.uuid4())
            hashed_password = generate_password_hash(password)

            user_document = {
                "_id": user_id,
                "email": email,
                "passwordHash": hashed_password,
                "fullName": data["fullName"],
                "phone": data["phone"],
                "isTeamMember": True,
                "createdAt": datetime.utcnow().isoformat(),
            }

            logger.info("✅ User document to insert: %s", user_document)  # Debug log
            self.user_collection.insert_one(user_document)
            logger.info("✅ User successfully inserted into database!")  # Debug log

            # Add user to the team
            user_to_team_data = {
                "userId": user_id,
                "teamId": invite["teamId"],
                "role": role,
            }
            add_result, status_code = self.user_to_team_repo.add_user_to_team(
                user_to_team_data
            )

            if status_code != 201:
                logger.error(
                    f"❌ Failed to add user to team: {add_result}"
                )  # Debug log
                self.user_collection.delete_one(
                    {"_id": user_id}
                )  # Rollback user creation
                return {"error": "Failed to add user to team."}, 500

            logger.info(
                f"✅ User successfully linked to team {invite['teamId']}"
            )  # Debug log

            # Update the team's members array with fullName and phone
            self.teams_collection.update_one(
                {"_id": invite["teamId"], "members.email": email},
                {
                    "$set": {
                        "members.$.userId": user_id,
                        "members.$.fullName": data["fullName"],
                        "members.$.phone": data["phone"],
                        "members.$.verified": True,
                    }
                },
            )
            logger.info(
                f"✅ Team {invite['teamId']} members updated with user details."
            )  # Debug log

            # Mark the invite as accepted
            self.invite_collection.update_one(
                {"_id": invite_token},
                {
                    "$set": {
                        "status": "accepted",
                        "acceptedAt": datetime.utcnow().isoformat(),
                    }
                },
            )
            logger.info("✅ Invitation marked as used")  # Debug log

            return {
                "message": "Team member registration successful!",
                "userId": user_id,
                "redirect_url": url_for("auth_bp.signin", _external=True),
            }, 201

        except KeyError as e:
            logger.error("Error during team member registration: %s", e)  # Debug log
            raise
        except Exception as e:
            logger.error(
                "Error during team member registration: %s", e, exc_info=True
            )  # Debug log
            raise


def validate_email(email):
    # ...existing code...
    domain = email.split("@")[-1]
    try:
        # For dnspython v2+, use resolve instead of query
        answers = dns.resolver.resolve(domain, "MX")
    except Exception as e:
        raise Exception(f"MX lookup failed for domain '{domain}': {e}")
    # ...existing code...


def validate_password(password):
    # Actual existing validation logic should be here (if any was originally present)
    if not password:
        return {"error": "Password is required."}, 400
    if len(password) < 8:
        return {"error": "Password must be at least 8 characters long."}, 400
    if not any(char.isdigit() for char in password) or not any(
        char.isalpha() for char in password
    ):
        return {"error": "Password must contain both letters and numbers."}, 400
    # If the function passed all checks, return None (indicating no error)
    return None
