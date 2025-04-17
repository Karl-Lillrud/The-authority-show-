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
import dns.resolver

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
            user_account = self.account_collection.find_one(
                {"userId": str(user["_id"])}
            )
            if not user_account:
                account_data = {
                    "_id": str(uuid.uuid4()),
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
        if user_account:
            return user_account

        if not team_list:
            return None

        first_team = team_list[0]
        team_id = first_team.get("_id")
        logger.info(f"🔹 First team details: {first_team}")
        logger.info(f"🔹 Team ID: {team_id}")

        owner_account = self._find_team_owner_account(team_id)
        if owner_account:
            return owner_account

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
                "_id": str(uuid.uuid4()),
                "userId": user_id,
                "email": email,
                "companyName": data.get("companyName", ""),
                "isCompany": data.get("isCompany", False),
                "subscriptionId": str(uuid.uuid4()),
                "creditId": str(uuid.uuid4()),
                "subscriptionStatus": "active",
                "createdAt": datetime.utcnow(),
                "referralBonus": 0,
                "subscriptionStart": datetime.utcnow(),
                "subscriptionEnd": None,
                "isActive": True,
                "created_at": datetime.utcnow(),
                "isFirstLogin": True,
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
            error_message = f"Error during registration: {str(e)}"
            status_code = 500
            if (
                isinstance(e, ValueError)
                and len(e.args) > 1
                and isinstance(e.args[1], dict)
            ):
                error_message = e.args[0]
                status_code = 400
            elif "duplicate key" in str(e).lower():
                error_message = "An account related error occurred. Please try again or contact support."
            return {"error": error_message}, status_code

    def register_team_member(self, data):
        try:
            logger.info("🔹 Received registration data: %s", data)
            invite_token = data.get("inviteToken")
            if not invite_token:
                logger.error("❌ Missing invite token")
                raise ValueError("Missing invite token")

            invite = self.invite_collection.find_one({"_id": invite_token})
            if not invite:
                logger.error(f"❌ Invalid invite token: {invite_token}")
                raise ValueError("Invalid invite token")

            role = invite.get("role")
            if not role:
                logger.error(f"❌ Missing role in invite: {invite}")
                raise KeyError("role")

            logger.info("✅ Role extracted from invite: %s", role)

            required_fields = ["email", "password", "fullName", "phone"]
            for field in required_fields:
                if field not in data or not data[field]:
                    logger.error(f"❌ Missing required field: {field}")
                    return {"error": f"Missing required field: {field}"}, 400

            email = data["email"].lower().strip()
            password = data["password"]

            if invite.get("status") != "pending":
                logger.error(f"❌ Invite is not pending: {invite}")
                return {"error": "Invite is not valid or already used."}, 400

            if invite["email"].lower() != email:
                logger.error(
                    f"❌ Email mismatch! Invited: {invite['email']} - Registering: {email}"
                )
                return {"error": "The email does not match the invitation."}, 400

            existing_user = self.user_collection.find_one({"email": email})
            if existing_user:
                logger.error("❌ Email already exists: %s", email)
                return {"error": "Email already registered."}, 409

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

            logger.info("✅ User document to insert: %s", user_document)
            self.user_collection.insert_one(user_document)
            logger.info("✅ User successfully inserted into database!")

            user_to_team_data = {
                "userId": user_id,
                "teamId": invite["teamId"],
                "role": role,
            }
            add_result, status_code = self.user_to_team_repo.add_user_to_team(
                user_to_team_data
            )

            if status_code != 201:
                logger.error(f"❌ Failed to add user to team: {add_result}")
                self.user_collection.delete_one({"_id": user_id})
                return {"error": "Failed to add user to team."}, 500

            logger.info(f"✅ User successfully linked to team {invite['teamId']}")

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
            )

            self.invite_collection.update_one(
                {"_id": invite_token},
                {
                    "$set": {
                        "status": "accepted",
                        "acceptedAt": datetime.utcnow().isoformat(),
                    }
                },
            )
            logger.info("✅ Invitation marked as used")

            return {
                "message": "Team member registration successful!",
                "userId": user_id,
                "redirect_url": url_for("auth_bp.signin", _external=True),
            }, 201

        except KeyError as e:
            logger.error("Error during team member registration: %s", e)
            raise
        except Exception as e:
            logger.error("Error during team member registration: %s", e, exc_info=True)
            raise


def validate_email(email):
    domain = email.split("@")[-1]
    try:
        answers = dns.resolver.resolve(domain, "MX")
    except Exception as e:
        raise Exception(f"MX lookup failed for domain '{domain}': {e}")


def validate_password(password):
    if not password:
        return {"error": "Password is required."}, 400
    if len(password) < 8:
        return {"error": "Password must be at least 8 characters long."}, 400
    if not any(char.isdigit() for char in password) or not any(
        char.isalpha() for char in password
    ):
        return {"error": "Password must contain both letters and numbers."}, 400
    return None
