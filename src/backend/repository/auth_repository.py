import uuid
from datetime import datetime
from flask import request, session, redirect, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from backend.database.mongo_connection import collection
from backend.services.authService import validate_password, validate_email
from backend.repository.account_repository import AccountRepository
from backend.repository.usertoteam_repository import UserToTeamRepository
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

            # Get user's personal account
            user_account = self.account_collection.find_one(
                {"userId": session["user_id"]}
            )

            # Get teams the user belongs to
            team_list = self._get_user_teams(session["user_id"])

            # Determine which account to use (personal or team)
            active_account = self._determine_active_account(user_account, team_list)
            if not active_account:
                return {"error": "No account or team-associated account found"}, 403

            # Prepare response data
            account_id = active_account.get("_id")
            redirect_url = "/podprofile" if user_account else "/podcastmanager"

            response = {
                "message": "Login successful",
                "redirect_url": redirect_url,
                "teams": team_list,
                "accountId": str(account_id),
                "isTeamMember": user.get("isTeamMember", False),
                "usingTeamAccount": bool(
                    not user_account and active_account != user_account
                ),
            }

            return response, 200

        except Exception as e:
            logger.error("Error during login: %s", e, exc_info=True)
            return {"error": f"Error during login: {str(e)}"}, 500

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
            return {"error": f"Error during registration: {str(e)}"}, 500

    def register_team_member(self, data):
        """Registers a new team member from an invite."""
        try:
            print("🔹 Received registration data:", data)  # Debugging

            invite_token = data.get("inviteToken")

            if not invite_token:
                print("❌ Missing invite token in request payload.")
                return {"error": "Missing invite token in request."}, 400

            required_fields = ["email", "password", "fullName", "phone"]
            for field in required_fields:
                if field not in data or not data[field]:
                    print(f"❌ Missing field: {field}")
                    return {"error": f"Missing required field: {field}"}, 400

            email = data["email"].lower().strip()
            password = data["password"]

            invite = self.invite_collection.find_one(
                {"_id": invite_token, "status": "pending"}
            )
            if not invite:
                print(f"❌ Invalid or expired invite: {invite_token}")
                return {"error": "Invalid or expired invite token."}, 400

            team_id = invite["teamId"]

            if invite["email"].lower() != email:
                print(
                    f"❌ Email mismatch! Invited: {invite['email']} - Registering: {email}"
                )
                return {"error": "The email does not match the invitation."}, 400

            existing_user = self.user_collection.find_one({"email": email})
            if existing_user:
                print("❌ Email already exists:", email)
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

            print("✅ User document to insert:", user_document)
            self.user_collection.insert_one(user_document)
            print("✅ User successfully inserted into database!")

            user_to_team_data = {"userId": user_id, "teamId": team_id, "role": "member"}
            add_result, status_code = self.user_to_team_repo.add_user_to_team(
                user_to_team_data
            )

            if status_code != 201:
                print(f"❌ Failed to add user to team: {add_result}")
                self.user_collection.delete_one({"_id": user_id})
                return {"error": "Failed to add user to team."}, 500

            print(f"✅ User successfully linked to team {team_id}")

            # Uppdatera teamets members-array med fullName och phone
            self.teams_collection.update_one(
                {"_id": team_id, "members.email": email},
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
                f"Updated team {team_id} members with fullName and phone: {data['fullName']}, {data['phone']}"
            )
            print(f"✅ Team {team_id} members updated with user details.")

            self.invite_collection.update_one(
                {"_id": invite_token},
                {
                    "$set": {
                        "status": "accepted",
                        "acceptedAt": datetime.utcnow().isoformat(),
                    }
                },
            )
            print("✅ Invitation marked as used")

            return {
                "message": "Team member registration successful!",
                "userId": user_id,
                "redirect_url": url_for("auth_bp.signin", _external=True),
            }, 201

        except Exception as e:
            print("❌ Error during registration:", e)
            logger.error("Error during team member registration: %s", e, exc_info=True)
            return {"error": f"Error during team member registration: {str(e)}"}, 500


def validate_email(email):
    # ...existing code...
    domain = email.split("@")[-1]
    try:
        # For dnspython v2+, use resolve instead of query
        answers = dns.resolver.resolve(domain, "MX")
    except Exception as e:
        raise Exception(f"MX lookup failed for domain '{domain}': {e}")
    # ...existing code...
