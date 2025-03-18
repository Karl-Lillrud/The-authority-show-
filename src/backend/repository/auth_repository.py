import uuid
from datetime import datetime
from flask import request, session, redirect, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from backend.database.mongo_connection import collection
from backend.services.authService import validate_password, validate_email
from backend.repository.account_repository import AccountRepository
from backend.repository.usertoteam_repository import UserToTeamRepository
import logging

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

            user = self.user_collection.find_one({"email": email})
            if not user or not check_password_hash(user["passwordHash"], password):
                return {"error": "Invalid email or password"}, 401

            session["user_id"] = str(user["_id"])
            session["email"] = user["email"]
            session.permanent = remember

            # Check if user has their own account
            user_account = self.account_collection.find_one({"userId": session["user_id"]})
            
            # Retrieve teams the user is part of
            team_membership, status_code = self.user_to_team_repo.get_teams_for_user(session["user_id"])
            team_list = team_membership.get("teams", []) if status_code == 200 else []
            
            logger.info(f"✅ User is part of teams: {team_list}")

            # Determine the correct main account (the team owner's account)
            main_account = None
            if team_list and not user_account:  # Only look for team account if user doesn't have their own
                first_team = team_list[0]
                logger.info(f"🔹 First team details: {first_team}")
                
                # Get the team ID
                team_id = first_team.get("_id")
                logger.info(f"🔹 Team ID: {team_id}")
                
                # Find the team owner's user ID (assuming role "creator" indicates ownership)
                team_owner_mapping = self.users_to_teams_collection.find_one(
                    {"teamId": team_id, "role": "creator"},
                    {"userId": 1}
                )
                
                if team_owner_mapping:
                    owner_id = team_owner_mapping.get("userId")
                    logger.info(f"🔹 Found team owner ID: {owner_id}")
                    
                    # Find the account associated with the owner ID
                    owner_account = self.account_collection.find_one({"userId": owner_id})
                    
                    if owner_account:
                        logger.info(f"🔹 Found account for team owner: {owner_account['_id']}")
                        main_account = owner_account
                    else:
                        logger.warning(f"⚠️ No account found for team owner with ID: {owner_id}")
                else:
                    logger.warning(f"⚠️ No creator found for team ID: {team_id}")
                    
                    # Fallback: try to find anyone with a role in the team
                    any_team_member = self.users_to_teams_collection.find_one(
                        {"teamId": team_id},
                        {"userId": 1}
                    )
                    
                    if any_team_member:
                        member_id = any_team_member.get("userId")
                        logger.info(f"🔹 Found team member ID: {member_id}")
                        
                        # Find the account associated with this member
                        member_account = self.account_collection.find_one({"userId": member_id})
                        
                        if member_account:
                            logger.info(f"🔹 Found account for team member: {member_account['_id']}")
                            main_account = member_account
            
            # Decide which account to use
            active_account = user_account or main_account
            if not active_account:
                return {"error": "No account or team-associated account found"}, 403

            account_id = active_account.get("_id")
            podcasts = list(self.podcast_collection.find({"accountId": account_id}))

            # Redirect team members to work under the main account
            redirect_url = "/podprofile" if user_account else "/podcastmanager"

            # Add debug info to response
            response = {
                "message": "Login successful",
                "redirect_url": redirect_url,
                "teams": team_list,
                "accountId": str(account_id),
                "isTeamMember": user.get("isTeamMember", False),
                "usingTeamAccount": bool(main_account and not user_account)
            }

            return response, 200

        except Exception as e:
            logger.error("Error during login: %s", e, exc_info=True)
            return {"error": f"Error during login: {str(e)}"}, 500

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

            account_response, status_code = self.account_repo.create_account(account_data)

            if status_code != 201:
                return {"error": "Failed to create account", "details": account_response}, 500

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

            invite = self.invite_collection.find_one({"_id": invite_token, "status": "pending"})
            if not invite:
                print(f"❌ Invalid or expired invite: {invite_token}")
                return {"error": "Invalid or expired invite token."}, 400

            team_id = invite["teamId"]

            if invite["email"].lower() != email:
                print(f"❌ Email mismatch! Invited: {invite['email']} - Registering: {email}")
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

            user_to_team_data = {
                "userId": user_id,
                "teamId": team_id,
                "role": "member"
            }
            add_result, status_code = self.user_to_team_repo.add_user_to_team(user_to_team_data)

            if status_code != 201:
                print(f"❌ Failed to add user to team: {add_result}")
                self.user_collection.delete_one({"_id": user_id})
                return {"error": "Failed to add user to team."}, 500

            print(f"✅ User successfully linked to team {team_id}")

            self.invite_collection.update_one(
                {"_id": invite_token},
                {"$set": {"status": "accepted", "acceptedAt": datetime.utcnow().isoformat()}}
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

