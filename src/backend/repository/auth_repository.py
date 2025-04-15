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

            # --- BEGIN: Add default data for new user ---
            try:
                # Check if this user already has podcasts (indicator of prior setup)
                podcast_check_response, podcast_check_status = (
                    self.podcast_repo.get_podcasts(user_id)
                )

                # Proceed only if the check was successful and returned no podcasts
                if podcast_check_status == 200 and not podcast_check_response.get(
                    "podcast"
                ):
                    logger.info(
                        f"✅ New user {user_id}. Creating default team, podcast, and episodes."
                    )
                    # 1. Create Default Podcast (linked to account and team)
                    podcast_data = {
                        "podName": "My Example Podcast",
                        "ownerName": email.split("@")[0],  # Example owner name
                        # accountId is derived from user_id within add_podcast
                        "teamId": "",  # Link podcast to the team
                        "logoUrl": "https://d3t3ozftmdmh3i.cloudfront.net/staging/podcast_uploaded_nologo/42425076/42425076-1731361782842-b9ba09e6cabe6.jpg",
                        "description": "This is a sample podcast created for demonstration purposes.",
                        "category": "Technology",
                        "language": "English",
                        "hostName": "Karl Lillrud",
                        "ownerName": "Karl Lillrud",
                        "podUrl": "https://www.example.com",
                    }

                    podcast_response, podcast_status = (
                        self.podcast_repo.add_podcast(user_id, podcast_data)
                    )

                    if podcast_status == 201:
                        podcast_id = podcast_response["podcast_id"]
                        logger.info(
                            f"✅ Default podcast created: {podcast_id} for user {user_id}"
                        )

                        # 2. Create Example Episodes
                        now = datetime.now(timezone.utc)
                        one_week_future = now + timedelta(days=7)
                        two_weeks_future = now + timedelta(days=14)

                        episode_data_1 = {
                            "podcastId": podcast_id,
                            "title": "Example Episode 1: Getting Started",
                            "description": "This is your first example episode, scheduled for next week.",
                            "publishDate": one_week_future.isoformat(),
                            "status": "Not Recorded",  # Changed from "Active" to "Not Recorded"
                            "recordingAt": one_week_future.isoformat(),
                            "duration": 45,
                            "isHidden": False,
                            "author": email.split("@")[0],
                        }
                        episode_data_2 = {
                            "podcastId": podcast_id,
                            "title": "Example Episode 2: Exploring Features",
                            "description": "Discover what you can do with PodManager, scheduled in two weeks.",
                            "publishDate": two_weeks_future.isoformat(),
                            "status": "Not Scheduled",  # Changed from "Active" to "Not Scheduled"
                            "recordingAt": two_weeks_future.isoformat(),
                            "duration": 60,
                            "isHidden": False,
                            "author": email.split("@")[0],
                        }

                        # Register Episode 1
                        ep1_resp, ep1_stat = self.episode_repo.register_episode(
                            episode_data_1, user_id
                        )
                        if ep1_stat == 201:
                            logger.info(
                                f"✅ Example episode 1 created for podcast {podcast_id}"
                            )
                        else:
                            logger.error(
                                f"❌ Failed to create example episode 1 for user {user_id}: {ep1_resp}"
                            )

                        # Register Episode 2
                        ep2_resp, ep2_stat = self.episode_repo.register_episode(
                            episode_data_2, user_id
                        )
                        if ep2_stat == 201:
                            logger.info(
                                f"✅ Example episode 2 created for podcast {podcast_id}"
                            )
                        else:
                            logger.error(
                                f"❌ Failed to create example episode 2 for user {user_id}: {ep2_resp}"
                            )
                    else:
                        logger.error(
                            f"❌ Failed to create default podcast for user {user_id}. Response: {podcast_response}"
                        )
                        # Optionally attempt to clean up team if podcast failed? Depends on requirements.
                    
                elif podcast_check_status != 200:
                    logger.warning(
                        f"⚠️ Could not verify podcast presence for user {user_id} (status {podcast_check_status}). Skipping default data creation."
                    )
                else:  # podcast_check_status == 200 and podcasts exist
                    logger.info(
                        f"ℹ️ User {user_id} already has podcasts. Skipping default data creation."
                    )

            except Exception as default_data_err:
                # Log error but don't fail registration
                logger.error(
                    f"❌ Error creating default data for user {user_id}: {default_data_err}",
                    exc_info=True,
                )
            # --- END: Add default data for new user ---

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
